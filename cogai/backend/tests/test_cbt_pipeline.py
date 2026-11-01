import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app.ai import AI, ChatReply, ModelRisk, OutputCheck, one_question
from app.cbt import advance
from app.config import Settings
from app.main import create_app
from app.pseudonyms import build, current, mask, unmask
from app.research import AppraisalField, AppraisalState, DeepView
from app.retrieval import KnowledgeIndex


def appraisal(**values):
    state = AppraisalState()
    for key, value in values.items():
        state.fields[key] = AppraisalField(value=value, evidence=['trích dẫn'])
    state.status = 'available'
    return state


GATED = dict(goal_relevance='high', goal_congruence='blocks_goal', certainty='low', agency='self', affect_intensity='medium')


def test_names_are_masked_consistently_and_restored():
    mapping = build(['Hôm nay em bị tổ trưởng Hùng nhắc.', 'Chị Lan và anh Nguyễn Văn Tú ở Hà Nội.', 'anh Tú về muộn', 'Bạn AnMi ơi, cảm ơn bạn Mầm.'])
    assert mapping['Hùng'] == '[NGƯỜI 1]' and mapping['Tú'] == mapping['Nguyễn Văn Tú']
    assert mask('tổ trưởng Hùng ở Hà Nội', mapping) == 'tổ trưởng [NGƯỜI 1] ở Hà Nội'
    assert 'AnMi' not in mapping and 'Mầm' not in mapping and 'Hà' not in mapping
    assert mask('Bạn AnMi nhắc mình nói với anh Hùng.', mapping) == 'Bạn AnMi nhắc mình nói với anh [NGƯỜI 1].'
    assert unmask({'reply': ['[NGƯỜI 1] nhắc bạn']}, mapping) == {'reply': ['Hùng nhắc bạn']}


def test_provider_never_receives_names_and_reply_keeps_them(tmp_path, monkeypatch):
    sent = []

    async def post(self, url, **kwargs):
        sent.append(json.dumps(kwargs['json'], ensure_ascii=False))
        return httpx.Response(200, request=httpx.Request('POST', url),
                              json={'choices': [{'message': {'content': '{"reply":"Bạn bị [NGƯỜI 1] nhắc."}'}}]})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    ai = AI(Settings(data_dir=tmp_path, mode='live', llm_api_key='fake'))
    token = current.set(build(['tổ trưởng Hùng nhắc em']))
    try:
        result = asyncio.run(ai.complete('Reply', {'text': 'tổ trưởng Hùng nhắc em'}, ChatReply,
                                         turns=[{'role': 'user', 'content': 'anh Hùng khó tính'}]))
    finally:
        current.reset(token)
    assert 'Hùng' not in sent[0] and '[NGƯỜI 1]' in sent[0]
    assert result.reply == 'Bạn bị Hùng nhắc.'


def test_one_question_per_reply():
    assert one_question('Bạn buồn lắm đúng không? Mình hiểu. Chuyện xảy ra khi nào? Ai ở đó?') == 'Bạn buồn lắm. Mình hiểu. Chuyện xảy ra khi nào?'
    assert one_question('Chào bạn, mình là AnMi.') == 'Chào bạn, mình là AnMi.'


def test_cbt_pacing_advances_one_step_and_respects_readiness():
    state = {'step': 'listen'}
    assert advance(state, appraisal(**GATED), 'Chắc em làm gì cũng hỏng', 1) == 'clarify'
    state['step'] = 'clarify'
    assert advance(state, appraisal(**GATED), 'Chỉ hôm nay thôi', 2) == 'identify'
    state['step'] = 'identify'
    assert advance(state, AppraisalState(), 'Em nghĩ mình vô dụng', 3) == 'evidence'
    state['step'] = 'evidence'
    assert advance(state, AppraisalState(), 'Chưa bị nhắc lần nào', 4) == 'evidence'
    assert advance(state, AppraisalState(), 'Chắc không bị đuổi', 5) == 'action'
    state['step'] = 'action'
    assert advance(state, AppraisalState(), 'Em sẽ nói với anh ấy', 6) == 'listen' and state['cues'] == {'dot': False, 'distortion': False}
    # Acute distress: validate first, do not start questioning thoughts.
    assert advance({'step': 'listen'}, appraisal(**{**GATED, 'affect_intensity': 'high'}), 'Em sụp đổ rồi', 1) == 'listen'
    # The user asks to just be heard: back to listening at once.
    assert advance({'step': 'evidence', 'cues': {'dot': True, 'distortion': True}}, appraisal(**GATED), 'Em chỉ muốn kể thôi, đừng phân tích', 4) == 'listen'


def card(card_id, crisis, fits, vector):
    return {'id': card_id, 'kind': 'safety_card', 'title': card_id, 'type': 't', 'triggers': [], 'goals': [], 'steps': [],
            'text': card_id, 'appraisal': '', 'cbt': '', 'source': 's', 'version': '1', 'license': 'l', 'review_status': 'draft',
            'reviewed_by': '', 'development_only': True, 'crisis': crisis, 'fits_steps': fits, 'vectors': [vector], 'embedding_model': 'm'}


def test_safety_card_choice_excludes_crisis_cards_and_weak_matches(tmp_path):
    index = KnowledgeIndex(tmp_path / 'k.sqlite3')
    index.ingest([card('crisis', True, [], [1, 0, 0]), card('reframe', False, ['evidence'], [.6, .8, 0]), card('sleep', False, [], [.62, .78, 0])])
    assert index.best_card([1, 0, 0], allow_development=True, model_version='m')['id'] == 'sleep'
    assert index.best_card([1, 0, 0], allow_development=True, model_version='m', step='evidence')['id'] == 'reframe'
    assert index.best_card([0, 0, 1], allow_development=True, model_version='m') is None
    assert index.best_card([1, 0, 0], model_version='m') is None  # drafts never outside development


def test_safety_plan_is_saved_privately_and_validated(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        client.post('/api/session', json={'accepted': True, 'adult': True, 'persist': True})
        assert client.get('/api/safety-plan').json() == {'empty': True}
        plan = {'warning_signs': ['mất ngủ nhiều đêm'], 'people': ['chị gái'], 'professionals': ['Cấp cứu 115']}
        assert client.put('/api/safety-plan', json=plan).json()['saved'] is True
        assert client.get('/api/safety-plan').json()['people'] == ['chị gái']
        assert client.put('/api/safety-plan', json={'coping': ['x'] * 7}).status_code == 422
        assert client.put('/api/safety-plan', json={'unknown': ['x']}).status_code == 422


def test_chat_paces_steps_from_appraisal_without_user_choosing(tmp_path, monkeypatch):
    app = create_app(Settings(data_dir=tmp_path, mode='live', llm_api_key='synthetic'))
    steps = []

    async def complete(task, data, schema, **kwargs):
        if schema is ModelRisk:
            return ModelRisk(level='low', reason='synthetic')
        if schema is AppraisalState:
            return appraisal(**{k: v for k, v in GATED.items()}).model_copy(update={'fields': {
                k: AppraisalField(value=v, evidence=[data['message'][:10]]) for k, v in {**{f: 'unknown' for f in AppraisalState().fields}, **GATED}.items()}})
        if schema is DeepView:
            return DeepView(observation='o', uncertainty='u', source_quotes=[], distortions=[{'type': 'overgeneralization', 'quote': 'làm gì cũng hỏng'}])
        if schema is ChatReply:
            steps.append(data['guidance']['step'])
            return ChatReply(reply='Mình đang nghe bạn. Chuyện xảy ra thế nào?')
        return OutputCheck(allow=True)
    monkeypatch.setattr(app.state.ai, 'complete', complete)
    with TestClient(app) as client:
        client.post('/api/session', json={'accepted': True, 'adult': True, 'external_ai': True, 'persist': True})
        first = client.post('/api/chat', json={'message': 'Chắc em làm gì cũng hỏng'}).json()
        assert first['step'] == 'listen' and first['next_step'] == 'clarify'
        second = client.post('/api/chat', json={'message': 'Chắc em làm gì cũng hỏng thật'}).json()
        assert second['step'] == 'clarify'
        assert client.post('/api/chat', json={'message': 'Chắc em làm gì cũng hỏng', 'action': 'listen'}).json()['step'] == 'listen'
        assert steps == ['listen', 'clarify', 'listen']
        session = app.state.store.session(client.cookies.get('cogai_session'))
        assert app.state.store.document(session, 'conversation')['thought'] == 'làm gì cũng hỏng'

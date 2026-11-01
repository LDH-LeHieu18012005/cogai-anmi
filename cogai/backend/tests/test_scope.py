from fastapi.testclient import TestClient

from app.ai import ChatReply, ModelRisk, OutputCheck
from app.config import Settings
from app.main import create_app
from app.research import AppraisalState
from app.safety import CHECK_IN_REPLY, OFF_TOPIC_REPLIES, SUPPORT_REPLY, off_topic_reply

OFF_TOPIC = {'Giải giúp mình phương trình x^2-5x+6=0', 'Viết code Python sắp xếp mảng',
             'Thời tiết Hà Nội mai thế nào'}


def live_client(tmp_path, monkeypatch, calls, level='low'):
    app = create_app(Settings(data_dir=tmp_path, mode='live', llm_api_key='synthetic'))

    async def complete(task, data, schema, **kwargs):
        calls.append(schema)
        if schema is ModelRisk:
            assert 'scope' in task and 'off_topic' in task
            message = data['latest_message']
            return ModelRisk(level=level, reason='synthetic', scope='off_topic' if message in OFF_TOPIC else 'in_scope')
        if schema is AppraisalState:
            return AppraisalState()
        if schema is ChatReply:
            assert '# Phạm vi' in task
            return ChatReply(reply='Nghe có vẻ hôm nay bạn mệt lắm. Điều gì nặng nhất với bạn?')
        return OutputCheck(allow=True)

    monkeypatch.setattr(app.state.ai, 'complete', complete)
    client = TestClient(app)
    client.__enter__()
    client.post('/api/session', json={'accepted': True, 'adult': True, 'external_ai': True, 'persist': True})
    return client


def test_off_topic_is_declined_with_fixed_wording_and_never_output_checked(tmp_path, monkeypatch):
    calls = []
    client = live_client(tmp_path, monkeypatch, calls)
    first = client.post('/api/chat', json={'message': 'Giải giúp mình phương trình x^2-5x+6=0'}).json()
    assert first['reply'] == OFF_TOPIC_REPLIES[0]
    assert first['risk']['scope'] == 'off_topic' and first['risk']['requires_support'] is False
    assert OutputCheck not in calls  # the draft (if any) was discarded unseen
    second = client.post('/api/chat', json={'message': 'Viết code Python sắp xếp mảng', 'channel': 'voice'}).json()
    assert second['reply'] == OFF_TOPIC_REPLIES[1]  # rotated, not repeated
    back = client.post('/api/chat', json={'message': 'Thật ra dạo này mình mệt vì làm ca'}).json()
    assert back['reply'].startswith('Nghe có vẻ') and back['risk']['scope'] == 'in_scope'
    assert OutputCheck in calls
    client.__exit__(None, None, None)


def test_safety_wins_over_scope(tmp_path, monkeypatch):
    client = live_client(tmp_path, monkeypatch, [], level='high')
    reply = client.post('/api/chat', json={'message': 'Thời tiết Hà Nội mai thế nào'}).json()
    assert reply['reply'] == SUPPORT_REPLY
    client.__exit__(None, None, None)


def test_off_topic_does_not_close_an_open_safety_question(tmp_path, monkeypatch):
    client = live_client(tmp_path, monkeypatch, [])
    assert client.post('/api/chat', json={'message': 'Mình không chịu nổi nữa'}).json()['reply'] == CHECK_IN_REPLY
    again = client.post('/api/chat', json={'message': 'Viết code Python sắp xếp mảng'}).json()
    assert again['reply'] == CHECK_IN_REPLY
    client.__exit__(None, None, None)


def test_off_topic_replies_suit_voice():
    for reply in OFF_TOPIC_REPLIES:
        assert reply.count('?') <= 1 and len(reply.split()) <= 50
    assert off_topic_reply([{'role': 'assistant', 'content': OFF_TOPIC_REPLIES[-1]}]) == OFF_TOPIC_REPLIES[0]

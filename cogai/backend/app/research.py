"""Paper-informed contracts, not a claim of reproducing CARE or EviOCEAN."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .ai import ProviderFailure

FIELD_VALUES = {
    'goal_relevance': {'low','medium','high'},
    'goal_congruence': {'supports_goal','blocks_goal','mixed','unclear'},
    'agency': {'self','other','shared','environment','unclear'},
    'certainty': {'low','medium','high'},
    'novelty': {'low','medium','high'},
    'moral_violation': {'low','medium','high'},
    'social_threat': {'low','medium','high'},
    'affect_intensity': {'low','medium','high'},
}


class AppraisalField(BaseModel):
    value: str = 'unknown'
    evidence: list[str] = Field(default_factory=list, max_length=3)
    confidence: float = Field(default=0, ge=0, le=1)


class AppraisalState(BaseModel):
    fields: dict[str, AppraisalField] = Field(default_factory=lambda: {k:AppraisalField() for k in FIELD_VALUES})
    status: Literal['available','unavailable'] = 'unavailable'
    version: str = 'care-text-adapter-v1'
    research_reproduced: bool = False

    @model_validator(mode='after')
    def validate_fields(self):
        if set(self.fields) != set(FIELD_VALUES):
            raise ValueError('Exactly eight CARE appraisal fields are required.')
        for key, field in self.fields.items():
            if field.value not in FIELD_VALUES[key] | {'unknown'}:
                raise ValueError('Invalid appraisal category')
            if field.value != 'unknown' and not field.evidence:
                raise ValueError('Non-unknown fields need source quotations.')
        return self


# The ten distortion types of the team's Mind-Reframe/Lumina DoT template.
DISTORTIONS = {
    'emotional_reasoning': 'Suy luận theo cảm xúc', 'overgeneralization': 'Khái quát hóa quá mức',
    'mental_filter': 'Lọc tiêu cực', 'should_statements': 'Câu "phải/nên" cứng nhắc',
    'all_or_nothing': 'Suy nghĩ trắng đen', 'mind_reading': 'Đoán ý người khác',
    'fortune_telling': 'Đoán trước điều xấu', 'magnification': 'Phóng đại',
    'personalization': 'Tự quy trách nhiệm', 'labeling': 'Dán nhãn',
}


class DistortionHypothesis(BaseModel):
    type: Literal[tuple(DISTORTIONS)]
    quote: str = Field(min_length=1, max_length=300)


class DeepView(BaseModel):
    observation: str = Field(max_length=1000)
    uncertainty: str = Field(max_length=500)
    source_quotes: list[str] = Field(max_length=4)
    # Distortion agent (CARE eq. 4): hypotheses only, each tied to the user's own words.
    distortions: list[DistortionHypothesis] = Field(default_factory=list, max_length=2)


class QueryViews(BaseModel):
    appraisal: str = Field(max_length=1800)
    cbt: str = Field(max_length=1800)


def gates(state, preceding_user_turns=0):
    v = {k:f.value for k,f in state.fields.items()}
    medium = lambda k: v[k] in {'medium','high'}
    r, b, u, i = medium('goal_relevance'), v['goal_congruence'] in {'blocks_goal','mixed'}, v['certainty']=='low', medium('affect_intensity')
    s, m = medium('social_threat'), medium('moral_violation')
    dot = r and (b or u or i)
    return {'dot':dot, 'distortion':dot and (u or v['agency'] in {'self','other','shared'} or s or m),
            'social':s or m or (v['agency'] in {'other','shared'} and b),
            'trait':preceding_user_turns>=4 and i and (s or b), 'visual':False,'acoustic':False}


class ResearchServices:
    def __init__(self, settings, ai=None):
        self.settings, self.ai = settings, ai

    async def project(self,text,side):
        if side not in {'query','document'} or self.ai is None or self.settings.mode!='live':
            raise ProviderFailure('Projection adapter not configured')
        # Paper tables 24 (appraisal, conditions 1/2) and 25 (CBT) in Vietnamese, asked in one call
        # instead of two to save latency. Both views are retrieval keys, never shown to the user.
        appraisal=('Điều kiện 1 – lời người chia sẻ: viết MỘT đoạn văn công thức hóa lâm sàng, bắt đầu bằng '
                   '"Người chia sẻ đánh giá tình huống...", nêu: 1) Tác nhân: sự kiện khách quan; 2) Đánh giá sơ cấp: '
                   'mối đe dọa tới mục tiêu, giá trị cốt lõi; 3) Đánh giá thứ cấp: quy trách nhiệm và khả năng đương đầu; '
                   '4) Cảm xúc cụ thể dẫn tới.' if side=='query' else
                   'Điều kiện 2 – phản hồi của người hỗ trợ: suy ngược trạng thái appraisal của người chia sẻ mà phản hồi này '
                   'nhắm tới, không tóm tắt lời khuyên. Viết MỘT đoạn bắt đầu bằng "Người chia sẻ có lẽ đang vật lộn với...", '
                   'nêu: 1) Tác nhân giả định; 2) Mục tiêu, giá trị bị đe dọa; 3) Khả năng đương đầu hạn chế hoặc tự trách; 4) Cảm xúc.')
        cbt=('Viết MỘT đoạn phản hồi giả định, lý tưởng của nhà trị liệu CBT thấu cảm cho '
             +('lời chia sẻ này' if side=='query' else 'tình huống mà phản hồi này giải quyết')+
             ', mô phỏng từ vựng, giọng điệu và nhịp của nhà trị liệu thật (khám phá, cùng xem xét, có thể xoay xở).')
        views=await self.ai.complete(
            'CogRAG: bạn là chuyên gia tâm lý lâm sàng AI về Lý thuyết Appraisal (Lazarus & Scherer) và nhà trị liệu CBT. '
            'Tạo hai biểu diễn để truy hồi, viết tiếng Việt, văn xuôi, không danh sách, mỗi biểu diễn 2–3 câu, tối đa 60 từ. '
            'appraisal: '+appraisal+' cbt: '+cbt+' Không thêm dữ kiện ngoài văn bản; đây không phải lời khuyên cho người dùng.',
            {'text':text},QueryViews,max_tokens=350)
        return {'appraisal':views.appraisal,'cbt':views.cbt}

    async def appraise(self, message, history, previous=None):
        if self.settings.mode != 'live' or self.ai is None:
            return AppraisalState()
        try:
            state = await self.ai.complete(
                'Trích xuất appraisal văn bản tám trường theo CARE. Dùng unknown khi thiếu bằng chứng, '
                'không đoán cảm xúc hoặc tính cách. evidence phải là trích nguyên văn lời người dùng. '
                'Trạng thái trước chỉ là tham khảo; cập nhật theo lời mới, giữ phản chứng và không ép kết luận. '
                'Mỗi trường tối đa một trích dẫn ngắn; unknown thì evidence rỗng. '
                'Các giá trị hợp lệ: '+str(FIELD_VALUES),
                {'message':message,'history':history[-6:],'previous':previous.model_dump() if previous else None},AppraisalState,
                max_tokens=900)
            source = '\n'.join(t['content'] for t in history if t['role']=='user')+'\n'+message
            # Reject unsupported model quotations instead of fabricating source attribution.
            for field in state.fields.values():
                if any(not q or q not in source for q in field.evidence):
                    raise ProviderFailure('Unsupported appraisal evidence')
            state.status, state.research_reproduced = 'available', False
            state.version = 'care-text-adapter-v1'
            return state
        except ProviderFailure:
            return AppraisalState()

    async def deepen(self, message, history, state):
        active = gates(state, sum(t['role']=='user' for t in history))
        # One text reasoning call covering the DoT, distortion and social agents that the
        # gates selected. Trait gate never runs without an independently consented trait adapter.
        if self.settings.mode != 'live' or not self.ai or not self.settings.research_deep_enabled or not (active['dot'] or active['social']):
            return {'status':'not_requested','gates':active}
        agents=[name for name in ('dot','distortion','social') if active[name]]
        try:
            view = await self.ai.complete('Phân tích chọn lọc theo các tác tử được gate bật: '+', '.join(agents)+'. '
                'dot: tách sự kiện quan sát được với suy nghĩ chủ quan, điều ủng hộ và chưa ủng hộ suy nghĩ đó. '
                'social: ý nghĩa quan hệ, chuẩn mực (trách móc, bị từ chối, mất mặt) mà không giả định nó đã xảy ra. '
                'distortion: nếu và chỉ nếu được bật, tối đa hai giả thuyết méo mó nhận thức thuộc danh sách '+str(DISTORTIONS)+
                ', mỗi giả thuyết kèm trích dẫn nguyên văn lời người dùng; không chắc thì để rỗng. '
                'Không chẩn đoán, không suy ra niềm tin cốt lõi. observation và uncertainty viết tiếng Việt, ngắn. '
                'source_quotes là trích nguyên văn lời người dùng.',
                {'message':message,'history':history[-6:],'appraisal':state.model_dump(),'gates':active},DeepView,max_tokens=700)
            source='\n'.join(t['content'] for t in history if t['role']=='user')+'\n'+message
            quotes=view.source_quotes+[d.quote for d in view.distortions]
            if any(not q or q not in source for q in quotes):
                raise ProviderFailure('Unsupported deep evidence')
            if not active['distortion']:
                view.distortions=[]
            result={'status':'available','gates':active,**view.model_dump()}
            result['distortions']=[{**d,'label':DISTORTIONS[d['type']]} for d in result['distortions']]
            return result
        except ProviderFailure:
            return {'status':'unavailable','gates':active}

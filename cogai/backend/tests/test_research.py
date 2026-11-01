import asyncio
import json

from app.config import Settings


def test_appraisal_unknown_is_not_fabricated_and_has_eight_fields(tmp_path):
    from app.research import AppraisalState, ResearchServices
    state = AppraisalState()
    assert len(state.fields) == 8
    assert all(value.value == 'unknown' and value.evidence == [] for value in state.fields.values())
    result = asyncio.run(ResearchServices(Settings(data_dir=tmp_path)).appraise('Tôi đi học', [], state))
    assert result.status == 'unavailable'
    assert result.research_reproduced is False


def test_knowledge_import_retrieves_three_views_only_when_approved(tmp_path):
    from app.retrieval import KnowledgeIndex
    index = KnowledgeIndex(tmp_path/'knowledge.sqlite3')
    card = {'id':'dev1','text':'kỳ thi học tập','appraisal':'mục tiêu học tập bị cản trở',
            'cbt':'xem xét bằng chứng kỳ thi','source':'urn:synthetic:test','version':'1',
            'license':'synthetic','review_status':'draft','reviewed_by':'','development_only':True}
    index.ingest([card])
    # Unreviewed starter cards are a development aid only, never outside development.
    assert index.retrieve('kỳ thi','học tập','bằng chứng')['items'] == []
    assert index.retrieve('kỳ thi','học tập','bằng chứng',allow_development=True)['items'][0]['id'] == 'dev1'
    index.ingest([{**card,'development_only':False}])
    assert index.retrieve('kỳ thi','học tập','bằng chứng',allow_development=True)['items'] == []
    card.update(review_status='approved',reviewed_by='test-reviewer')
    index.ingest([card])
    assert index.retrieve('kỳ thi','học tập','bằng chứng')['items'] == []
    result = index.retrieve('kỳ thi','học tập','bằng chứng',allow_development=True)
    assert result['method'] == 'lexical-development-baseline'
    assert result['items'][0]['source'] == 'urn:synthetic:test'
    assert len(result['items'][0]['scores']) == 3
    card['review_status']='withdrawn'
    index.ingest([card])
    assert index.retrieve('kỳ thi','học tập','bằng chứng',allow_development=True)['items'] == []


def test_missing_knowledge_is_empty_not_seeded(tmp_path):
    from app.retrieval import KnowledgeIndex
    index=KnowledgeIndex(tmp_path/'empty.sqlite3')
    assert index.retrieve('tôi lo về công việc','','')['items'] == []


def test_offline_and_online_semantic_pipeline_share_encoder(tmp_path):
    from app.retrieval import CognitivePipeline, KnowledgeIndex
    class Encoder:
        model_version='synthetic-encoder-v1'
        async def encode(self,texts):
            return [[1.,0.] for _ in texts]
    class Projector:
        async def project(self,text,side):
            assert side in {'document','query'}
            return {'appraisal':'synthetic appraisal','cbt':'synthetic CBT'}
    index=KnowledgeIndex(tmp_path/'semantic.sqlite3')
    pipeline=CognitivePipeline(index,Projector(),Encoder())
    card={'id':'s1','text':'synthetic source text','source':'urn:test:source','version':'1',
          'license':'synthetic','review_status':'approved','reviewed_by':'test-reviewer','development_only':True}
    asyncio.run(pipeline.prepare([card]))
    assert asyncio.run(pipeline.retrieve('query'))['items']==[]
    result=asyncio.run(pipeline.retrieve('query',allow_development=True))
    assert result['method']=='three-view-semantic-adapter'
    assert result['items'][0]['scores']==[1.,1.,1.]
    assert result['items'][0]['source']=='urn:test:source'


def test_encoder_rejects_nonfinite_or_mismatched_vectors(tmp_path):
    import pytest
    from app.retrieval import CognitivePipeline, KnowledgeIndex
    class Encoder:
        model_version='bad'
        async def encode(self,texts):return [[float('nan')]]*len(texts)
    class Projector:
        async def project(self,text,side):return {'appraisal':'a','cbt':'b'}
    pipeline=CognitivePipeline(KnowledgeIndex(tmp_path/'bad.sqlite3'),Projector(),Encoder())
    with pytest.raises(ValueError):
        asyncio.run(pipeline.prepare([{'id':'bad','text':'synthetic'}]))


def test_personality_contract_abstains_without_validated_direction():
    from app.personality import arbitrate
    assert arbitrate(False,False)=='insufficient_evidence'
    assert arbitrate(True,False)=='high'
    assert arbitrate(False,True)=='low'
    assert arbitrate(True,True)=='needs_arbitration'

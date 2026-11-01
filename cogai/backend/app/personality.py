"""EviOCEAN adapter contracts. Product abstention differs from paper fallback."""
import time
from typing import Literal, Protocol

from fastapi import HTTPException
from pydantic import BaseModel, Field

Indicator=Literal['emotions','cognition','sociality','motivation_goals','behavior_habits','self_concept_identity','environment_context']


class PersonalityEvidence(BaseModel):
    indicator: Indicator
    record_ids: list[str] = Field(min_length=1)
    direct_evidence: str
    counter_evidence: str = ''
    author_owned: bool
    stability: Literal['temporary','recurring','unknown']
    scope: Literal['single_context','multiple_contexts','unknown']


class EviOceanAdapter(Protocol):
    """Implement summary, seven indicators, independent high/low and arbitration.

    All referenced record IDs must belong to the authorized source set. Validators
    must not see preliminary labels or each other's judgments. No adapter ships
    as validated by default.
    """
    async def infer(self, records: list[dict]) -> dict: ...


def arbitrate(high_valid,low_valid):
    if high_valid and low_valid:
        return 'needs_arbitration'
    if high_valid:
        return 'high'
    if low_valid:
        return 'low'
    # Deliberate product policy: abstain instead of paper Eq. 7 preliminary fallback.
    return 'insufficient_evidence'


def run_job(store,session):
    try:
        with store.connection() as db:
            store.validate(db,session)
        if not session['consent']['personalization']:
            return
        records=[r for r in store.records(session,None) if r['kind']=='chat' and r['payload'].get('conversation_id')]
        conversations={r['payload']['conversation_id'] for r in records}
        result={'status':'insufficient_evidence' if len(conversations)<3 else 'adapter_unavailable',
                'traits':{},'evidence':[], 'source_conversations':len(conversations),
                'source_record_ids':[r['id'] for r in records],
                'method':'eviocean-interface-v1','research_reproduced':False,
                'missing':['validated summary/indicator/high-low/arbitrator adapters','Vietnamese evaluation'],
                'product_policy':'abstain_without_validated_evidence','updated':time.time()}
        store.put_document(session,'personality','personality',result)
        store.remove_documents(session,'personality_job')
    except HTTPException:
        return  # Revocation/deletion/logout cancels stale work.

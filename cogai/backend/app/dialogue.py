"""One journey shared by chat and optional Lumina exercises."""
import asyncio
import time
import uuid
from contextvars import ContextVar

from . import pseudonyms
from .cbt import advance
from .models import ReframeInput, Risk
from .research import AppraisalState, ResearchServices
from .retrieval import CognitivePipeline, KnowledgeIndex, ProviderEncoder
from .ai import ProviderFailure
from .safety import off_topic_reply, support_reply

STEPS = {'listen','clarify','identify','evidence','perspective','action'}
# Set by a request that will read the reply aloud. Called with each draft before the
# output check, so speech can be prepared in parallel; it is served only if the
# same text is later saved as the checked reply.
draft_ready: ContextVar = ContextVar('cogai_draft_ready', default=None)
# Set by a desk device. Called with a reply that has passed the output check, before the
# CARE appraisal for the next turn finishes, so speech is not held back by it. The caller
# must still compare against the reply chat() finally returns (final_gate may replace it).
reply_ready: ContextVar = ContextVar('cogai_reply_ready', default=None)
EMPTY_RETRIEVAL = {'items':[],'card':None,'method':'retrieval-unavailable','research_reproduced':False}


class Dialogue:
    def __init__(self,store,ai,config):
        self.store,self.ai,self.config=store,ai,config
        self.research=ResearchServices(config,ai)
        self.knowledge=KnowledgeIndex(config.data_dir/'knowledge.sqlite3')
        self.pipeline=CognitivePipeline(self.knowledge,self.research,ProviderEncoder(config))

    def state(self,session):
        return self.store.document(session,'conversation',{}) or {
            'conversation_id':str(uuid.uuid4()),'step':'listen','next_step':'listen','turns':[], 'risk':None,
            'situation':'','thought':'','appraisal':AppraisalState().model_dump()}

    def safety_event(self,session,channel,risk,resolve_check_in=False):
        event={'id':str(uuid.uuid4()),'channel':channel,'level':risk.level,'source':risk.source,
               'created':time.time(),'policy_version':'development-v3',
               'status':'service_error' if risk.level=='unavailable' else 'needs_support' if risk.level=='high' else 'needs_clarification' if risk.level=='check_in' else 'no_signal'}
        self.store.record_safety(session,event,risk.model_dump(),resolve_check_in=resolve_check_in)
        return event

    @staticmethod
    def resolves_check_in(active,risk):
        # A context-aware model answer after the clarifying question may close
        # check_in. Rules alone cannot: a bare "có" has no keyword to match. An off-topic
        # request is not an answer to the safety question, so the question stays open.
        return (active.get('level')=='check_in' and risk.level=='low' and risk.source=='model'
                and risk.scope=='in_scope')

    async def check(self,session,text,history):
        active=self.store.document(session,'safety',{})
        if active.get('level')=='high':
            return Risk.model_validate(active)
        risk=await self.ai.risk(text,history)
        if self.resolves_check_in(active,risk):
            return risk
        rank={'low':0,'unavailable':0,'check_in':1,'high':2}
        if active.get('level') in {'high','check_in'} and rank[active['level']]>rank[risk.level]:
            return Risk.model_validate(active)
        return risk

    def final_gate(self,session,result,exercise=False,resolved=False):
        active=self.store.document(session,'safety',{})
        rank={'low':0,'unavailable':0,'check_in':1,'high':2}
        if resolved and active.get('level')=='check_in':
            active={}
        if active.get('level') in {'high','check_in'} and rank[active['level']]>rank[result['risk']['level']]:
            risk=Risk.model_validate(active)
            # Drop all tool/retrieval material if a newer channel has raised a signal.
            return {'blocked':True,'message':support_reply(risk),'risk':risk.model_dump(),'mode':self.config.mode} if exercise else {
                'reply':support_reply(risk),'risk':risk.model_dump(),'mode':self.config.mode}
        return result

    def development(self):
        return self.config.knowledge_development and self.config.environment!='production'

    async def chat(self,session,data):
        state=self.state(session)
        history=state['turns']
        # Existing consenting guests can recover their pre-migration chat records.
        if not history and not self.store.document(session,'conversation'):
            history=self.store.chat_history(session)['turns']
        # A step the user picks wins; otherwise AnMi paces itself from the last turn's appraisal.
        action=data.action or state.get('next_step') or 'listen'
        if action not in STEPS:
            action='listen'
        names=pseudonyms.current.set(pseudonyms.build([t['content'] for t in history]+[data.message]))
        try:
            result,resolved=await self.respond(session,data,state,history,action)
        except BaseExceptionGroup as failure:
            # Surface the first HTTPException/consent revocation exactly as a sequential call would.
            raise failure.exceptions[0] from None
        finally:
            pseudonyms.current.reset(names)
        result=self.final_gate(session,result,resolved=resolved)
        final_risk=Risk.model_validate(result['risk'])
        if final_risk.requires_support:
            state['step']='service_unavailable' if final_risk.level=='unavailable' else 'support'
            state['next_step']='listen'
        self.safety_event(session,'chat',final_risk,resolve_check_in=resolved and final_risk.level=='low')
        return self.finish(session,data,state,history,result)

    def guidance(self,state,action,channel,retrieved):
        appraisal={k:v for k,v in state['appraisal'].get('fields',{}).items() if v.get('value')!='unknown'}
        deep=state.get('deep') or {}
        return {'step':action,'channel':channel,'appraisal':appraisal,
                'deep':{k:deep[k] for k in ('observation','uncertainty','distortions') if k in deep},
                'situation':state.get('situation',''),'thought':state.get('thought',''),
                'sources':[{'text':i['text'],'source':i['source']} for i in retrieved['items']],'card':retrieved.get('card')}

    async def safe_draft(self,message,history,guidance):
        try:
            return await self.ai.draft(message,history,guidance)
        except ProviderFailure:
            return None

    async def retrieve(self,message,channel,context='',step=None):
        if not (self.config.embedding_model and self.config.mode=='live'):
            return {**self.knowledge.retrieve(message,'','',allow_development=self.development()),'card':None}
        # The appraisal/CBT projections cost a model call on the critical path; use them where
        # cognitive matching matters most (working on a thought), semantic matching elsewhere.
        full=channel!='voice' and step in {'identify','evidence','perspective'}
        try:
            return await self.pipeline.retrieve(message,allow_development=self.development(),full=full,
                                                context=context,step=step)
        except (ProviderFailure,ValueError):
            return EMPTY_RETRIEVAL

    async def respond(self,session,data,state,history,action):
        live=self.config.mode=='live'
        previous=AppraisalState.model_validate(state['appraisal'])
        lumina=action=='perspective' and bool(state['thought'])
        async with asyncio.TaskGroup() as group:
            # Risk, appraisal, CogRAG retrieval and the reply draft run concurrently (brief 1.3:
            # the independent risk tier runs in parallel). Nothing is shown or stored until risk
            # is known and the draft has passed the separate output check; a risky turn discards it.
            risk_task=group.create_task(self.check(session,data.message,history))
            async def understood():
                # CARE appraisal, then the agents its gates select, in parallel with the reply.
                appraisal=await self.research.appraise(data.message,history,previous)
                return appraisal,await self.research.deepen(data.message,history,appraisal)
            appraisal_task=group.create_task(understood()) if live else None
            retrieval_task=group.create_task(self.retrieve(data.message,data.channel,state.get('situation',''),action))

            async def drafted():
                retrieved=await retrieval_task
                return await self.safe_draft(data.message,history,self.guidance(state,action,data.channel,retrieved))
            draft_task=group.create_task(drafted()) if live and not lumina else None
            risk=await risk_task
            active=self.store.document(session,'safety',{})
            resolved=self.resolves_check_in(active,risk)
            rank={'low':0,'unavailable':0,'check_in':1,'high':2}
            if not resolved and active.get('level') in {'high','check_in'} and rank[active['level']]>rank[risk.level]:
                risk=Risk.model_validate(active)
            if risk.requires_support:
                for task in (draft_task,appraisal_task,retrieval_task):
                    if task:
                        task.cancel()
                result={'reply':support_reply(risk),'risk':risk.model_dump(),'mode':self.config.mode}
                state['step']='support' if risk.level!='unavailable' else 'service_unavailable'
                return result,resolved
            if risk.scope=='off_topic':
                # Outside AnMi's remit: decline with fixed wording; the CBT cycle and its slots are left as they were.
                for task in (draft_task,appraisal_task,retrieval_task):
                    if task:
                        task.cancel()
                return {'reply':off_topic_reply(history),'risk':risk.model_dump(),'mode':self.config.mode},resolved
            # CBT slots of this cycle: the situation is where it started; the automatic thought
            # comes from the distortion agent's quote (below) or the reply to an identify question.
            if not state['situation'] or data.action=='clarify':
                state['situation']=data.message
            if data.action=='identify' or (state.get('step')=='identify' and not state['thought']):
                state['thought']=data.message
            state['step']=action
            retrieved=await retrieval_task
            if lumina:
                tool=await self.ai.reframe(ReframeInput(situation=state['situation'],thought=state['thought']),risk=risk)
                result={'reply':tool.get('message') or '\n'.join(c['reframe'] for c in tool.get('candidates',[])),
                        'risk':tool['risk'],'mode':self.config.mode,'tool':'lumina','exercise':tool}
            elif not live:
                result=await self.ai.chat(data.message,history,risk=risk)
            else:
                reply=await draft_task
                if not reply:
                    # One retry for a transient provider error before telling the user.
                    reply=await self.safe_draft(data.message,history,self.guidance(state,action,data.channel,retrieved))
                hook=draft_ready.get()
                if reply and hook:
                    hook(reply)
                result=await self.ai.checked(reply,risk) if reply else self.ai.withheld(risk)
                ready=reply_ready.get()
                if ready and not result['risk']['requires_support']:
                    ready(result['reply'])
            result['retrieval']={k:retrieved.get(k) for k in ('method','weights','research_reproduced')}|{
                'items':[{k:i[k] for k in ('id','source','score')} for i in retrieved['items']],
                'card':{k:retrieved['card'][k] for k in ('id','title','score')} if retrieved.get('card') else None}
            if result['risk']['requires_support']:
                state['step']='service_unavailable' if result['risk']['level']=='unavailable' else 'support'
            appraisal=previous
            if appraisal_task:
                # CARE appraisal (and the agents its gates select) informs the next turn.
                appraisal,state['deep']=await appraisal_task
                state['appraisal']=appraisal.model_dump()
                if state['deep'].get('distortions') and action in {'listen','clarify','identify'}:
                    state['thought']=state['deep']['distortions'][0]['quote']
            if not result['risk']['requires_support']:
                state['next_step']=advance(state,appraisal,data.message,sum(t['role']=='user' for t in history)+1)
                if state['next_step']=='listen' and action!='listen':
                    state['situation'],state['thought']='',''  # cycle closed; the next topic starts fresh
        return result,resolved

    def finish(self,session,data,state,history,result):
        state['turns']=(history+[{'role':'user','content':data.message},{'role':'assistant','content':result['reply']}])[-12:]
        state['risk']=result['risk']
        result.update(step=state['step'],next_step=state.get('next_step','listen'),conversation_id=state['conversation_id'],appraisal=state['appraisal'])
        # Validate revision again at every write: revoked in-flight responses cannot persist.
        result['record_id']=self.store.save(session,'chat',{'message':data.message,**result})
        self.store.put_document(session,'conversation','conversation',state)
        return result

    async def reframe(self,session,data):
        state=self.state(session)
        names=pseudonyms.current.set(pseudonyms.build([data.situation,data.thought,data.previous,data.feedback]))
        try:
            risk=await self.check(session,'\n'.join([data.situation,data.thought,data.feedback,data.previous]),state['turns'])
            result=await self.ai.reframe(data,risk=risk)
        finally:
            pseudonyms.current.reset(names)
        result=self.final_gate(session,result,exercise=True)
        final_risk=Risk.model_validate(result['risk'])
        self.safety_event(session,'exercise',final_risk)
        state.update(situation=data.situation,thought=data.thought,risk=result['risk'],next_step='listen',
                     step='service_unavailable' if final_risk.level=='unavailable' else 'support' if final_risk.requires_support else 'action')
        reply=result.get('message') or '\n'.join(c['reframe'] for c in result.get('candidates',[]))
        state['turns']=(state['turns']+[{'role':'user','content':data.situation+'\n'+data.thought},
                                     {'role':'assistant','content':reply}])[-12:]
        result.update(conversation_id=state['conversation_id'],step=state['step'])
        result['record_id']=self.store.save(session,'reframe',{'input':data.model_dump(),**result})
        self.store.put_document(session,'conversation','conversation',state)
        return result

"""CogRAG adapter: offline three-view document index, safety-planning cards, lexical dev baseline.

Weights follow the best CounselChat setting in the paper (Table 15: 0.5/0.3/0.2).
Draft (unreviewed) cards are usable only in development; production needs approved cards.
"""
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Protocol
import httpx

from .ai import ProviderFailure, external_guard
from .provider_budget import ProviderBudget
from .safety import redact
from .pseudonyms import mask


class SemanticEncoder(Protocol):
    model_version: str

    async def encode(self, texts: list[str]) -> list[list[float]]: ...


def cosine(a, b):
    if len(a) != len(b) or not a:
        return 0.0
    denominator=math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b))/denominator if denominator else 0.0


WEIGHTS=(.5,.3,.2)
CARD_MIN_SCORE=.33   # below this a card is a poor match for short Vietnamese turns; use none
CARD_STEP_BONUS=.06  # prefer the card that fits the current CBT step


def usable(card,allow_development):
    if card['review_status']=='approved':
        return allow_development or not card['development_only']
    # Unreviewed starter material is a development aid, never shown in production.
    return allow_development and card['review_status']=='draft' and card['development_only']


def lexical(a, b):
    x,y = Counter(re.findall(r'\w+',a.casefold())),Counter(re.findall(r'\w+',b.casefold()))
    denominator=math.sqrt(sum(v*v for v in x.values())*sum(v*v for v in y.values()))
    return sum(v*y[k] for k,v in x.items())/denominator if denominator else 0.0


class KnowledgeIndex:
    def __init__(self,path: Path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS cards (id TEXT PRIMARY KEY, body TEXT NOT NULL)')

    def available(self,allow_development=False):
        with sqlite3.connect(self.path) as db:
            cards=[json.loads(r[0]) for r in db.execute('SELECT body FROM cards')]
        return any(c.get('kind','document')=='document' and usable(c,allow_development) for c in cards)

    def ingest(self,cards):
        validated=[]
        for item in cards:
            required={'id','text','appraisal','cbt','source','version','license','review_status','reviewed_by','development_only'}
            if not required <= item.keys() or item['review_status'] not in {'draft','approved','withdrawn'}:
                raise ValueError('Each card needs provenance, three views and review metadata.')
            if any(not isinstance(item[k],str) or len(item[k])>20000 for k in required-{'development_only'}):
                raise ValueError('Invalid card metadata')
            if not isinstance(item['development_only'],bool):
                raise ValueError('development_only must be explicit boolean')
            if item['review_status']=='approved' and not item['reviewed_by']:
                raise ValueError('Approved cards require an actual reviewer attribution.')
            card={**item,'sha256':hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
            validated.append(card)
        with sqlite3.connect(self.path) as db:
            db.executemany('INSERT INTO cards VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                           [(item['id'],json.dumps(item,ensure_ascii=False)) for item in validated])

    def retrieve(self,semantic,appraisal,cbt,*,allow_development=False,query_vectors=None,model_version=None):
        with sqlite3.connect(self.path) as db:
            cards=[json.loads(row[0]) for row in db.execute('SELECT body FROM cards')]
        hits=[]
        for card in cards:
            if card.get('kind','document')!='document' or not usable(card,allow_development):
                continue
            if query_vectors is not None:
                if card.get('embedding_model') != model_version or not card.get('vectors'):
                    continue
                # Voice uses only the semantic view to stay fast; text uses all three (eq. 4).
                scores=[cosine(q,d) for q,d in zip(query_vectors,card['vectors'])]
                if len(scores) not in {1,3}:
                    continue
            elif allow_development:
                scores=[lexical(q,card[k]) for q,k in zip((semantic,appraisal,cbt),('text','appraisal','cbt'))]
            else:
                continue  # semantic adapter missing: do not relabel lexical matching as CogRAG.
            fused=scores[0] if len(scores)==1 else sum(w*s for w,s in zip(WEIGHTS,scores))
            if fused>0:
                hits.append({**{k:card[k] for k in ('id','text','source','version','sha256','development_only')},
                             'scores':scores,'score':fused})
        hits.sort(key=lambda x:(-x['score'],x['id']))
        method=('semantic-only' if query_vectors is not None and len(query_vectors)==1 else 'three-view-semantic-adapter'
                if query_vectors is not None else 'lexical-development-baseline' if allow_development else 'semantic-adapter-unavailable')
        return {'items':hits[:3],'method':method,'weights':list(WEIGHTS),'research_reproduced':False}

    def best_card(self,query_vector,*,allow_development=False,model_version=None,step=None,crisis=False):
        """c* = Top1 sim(phi(q), v_c) over safety-planning cards (paper section 3.4.2).

        Product additions: crisis cards only when risk calls for them (a low-risk turn
        must not be steered towards self-harm questions), a small bonus for the card
        that fits the current CBT step, and a minimum score.
        """
        with sqlite3.connect(self.path) as db:
            cards=[json.loads(row[0]) for row in db.execute('SELECT body FROM cards')]
        scored=[(cosine(query_vector,c['vectors'][0])+(CARD_STEP_BONUS if step in c.get('fits_steps',[]) else 0),c)
                for c in cards if c.get('kind')=='safety_card' and usable(c,allow_development) and bool(c.get('crisis'))==crisis
                and c.get('embedding_model')==model_version and c.get('vectors')]
        if not scored:
            return None
        score,card=max(scored,key=lambda x:x[0])
        if score<CARD_MIN_SCORE:
            return None
        return {**{k:card[k] for k in ('id','title','type','triggers','goals','steps','source','review_status')},'score':round(score,4)}


def checked_vectors(vectors,count):
    if len(vectors)!=count or not vectors or not vectors[0]:
        raise ValueError('Invalid embedding count or empty vector')
    size=len(vectors[0])
    if any(len(v)!=size or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in v) for v in vectors):
        raise ValueError('Embedding dimensions or values invalid')
    return vectors


class ProviderEncoder:
    def __init__(self,settings):
        self.settings=settings
        self.budget=ProviderBudget(settings)
        self.model_version=settings.embedding_model

    async def encode(self,texts):
        if not self.model_version or not self.settings.llm_api_key:
            raise ProviderFailure('Embedding adapter not configured')
        guard=external_guard.get()
        if guard:
            guard()
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                self.budget.reserve()
                response=await client.post(self.settings.llm_base_url.rstrip('/')+'/embeddings',
                    headers={'Authorization':'Bearer '+self.settings.llm_api_key},
                    json={'model':self.model_version,'input':[mask(redact(t)) for t in texts]})
                response.raise_for_status()
                rows=sorted(response.json()['data'],key=lambda row:row['index'])
                if [r['index'] for r in rows]!=list(range(len(texts))):
                    raise ValueError('Embedding index mismatch')
                return checked_vectors([r['embedding'] for r in rows],len(texts))
        except (httpx.HTTPError,KeyError,ValueError,TypeError) as exc:
            raise ProviderFailure('Embedding service unavailable or invalid') from exc


class CognitivePipeline:
    """Same encoder on both sides, offline A(d)/R(d), online A(q)/R(q).

    Projections are a transparent paper-informed implementation, not the authors'
    code, checkpoint, prompts or validated Vietnamese method.
    """
    def __init__(self,index,projector,encoder):
        self.index,self.projector,self.encoder=index,projector,encoder

    async def prepare(self,cards):
        prepared=[]
        for card in cards:
            if card.get('kind')=='safety_card':
                # Cards are matched on meaning only (paper eq. 7): one embedding of the key fields.
                card={**card,'text':card_text(card),'appraisal':'','cbt':''}
                prepared.append({**card,'vectors':checked_vectors(await self.encoder.encode([card['text']]),1),
                                 'embedding_model':self.encoder.model_version})
                continue
            views=await self.projector.project(card['text'],'document')
            vectors=checked_vectors(await self.encoder.encode([card['text'],views['appraisal'],views['cbt']]),3)
            prepared.append({**card,**views,'vectors':vectors,'embedding_model':self.encoder.model_version,
                             'projection_version':'cograg-paper-adapter-v1'})
        self.index.ingest(prepared)
        return len(prepared)

    async def retrieve(self,text,allow_development=False,full=True,context='',step=None):
        """full: A(q)/R(q) projection + three views (text). Otherwise semantic only (voice latency).

        `context` (the situation of the current CBT cycle) is embedded with the turn for
        card choice, so a short answer like "chỉ hôm nay thôi" still matches the topic.
        """
        if not self.index.available(allow_development):
            return {'items':[],'card':None,'method':'no-approved-corpus','research_reproduced':False}
        card_query=(context+'\n'+text).strip() if context and context!=text else text
        extra=[card_query] if card_query!=text else []
        if full:
            views=await self.projector.project(text,'query')
            vectors=checked_vectors(await self.encoder.encode([text,views['appraisal'],views['cbt'],*extra]),3+len(extra))
        else:
            views={'appraisal':'','cbt':''}
            vectors=checked_vectors(await self.encoder.encode([text,*extra]),1+len(extra))
        query_vectors,card_vector=(vectors[:-1],vectors[-1]) if extra else (vectors,vectors[0])
        result=self.index.retrieve(text,views['appraisal'],views['cbt'],allow_development=allow_development,
                                   query_vectors=query_vectors,model_version=self.encoder.model_version)
        result['card']=self.index.best_card(card_vector,allow_development=allow_development,
                                            model_version=self.encoder.model_version,step=step)
        return result


def expand_bundle(data):
    """Accept a plain card list or a bundle {defaults, documents, safety_cards} (app/knowledge/*.json)."""
    if isinstance(data, list):
        return data
    defaults=data.get('defaults',{})
    documents=[{**defaults,'appraisal':'','cbt':'',**item,'kind':'document'} for item in data.get('documents',[])]
    cards=[{**defaults,**item,'kind':'safety_card'} for item in data.get('safety_cards',[])]
    for card in cards:
        card.update(text=card_text(card),appraisal='',cbt='')
    return documents+cards


def card_text(card):
    """Concatenation of the key fields embedded for a safety-planning card."""
    return '\n'.join([card['title'],'Loại: '+card['type'],'Khi nào: '+'; '.join(card['triggers']),
                      'Mục tiêu: '+'; '.join(card['goals']),'Các bước: '+'; '.join(card['steps']),
                      'Ví dụ: '+' '.join(card.get('examples',[]))])

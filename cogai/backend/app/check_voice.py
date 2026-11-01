"""Explicit low-cost live probe: at most three requests, no retries or secrets in output."""
import asyncio
import json

import httpx
from fastapi import HTTPException

from .ai import AI, ChatReply, ProviderFailure
from .config import Settings


async def check():
    # Only the application process loads .env. Never print Settings or raw errors.
    config=Settings(mode='live',llm_base_url='https://api.openai.com/v1',
        llm_model='gpt-4.1-mini',external_daily_call_limit=0,llm_max_completion_tokens=128)
    result={'chat':False,'speech':False,'transcription':False,'requests_attempted':0}
    if not config.llm_api_key:
        return {**result,'error':'missing_key'}
    ai=AI(config)
    try:
        result['requests_attempted']+=1
        await ai.complete('Return a greeting of at most five Vietnamese words.',{},ChatReply)
        result['chat']=True
        async with httpx.AsyncClient(timeout=30) as client:
            ai.budget.reserve()
            result['requests_attempted']+=1
            speech=await client.post(config.llm_base_url+'/audio/speech',
                headers={'Authorization':'Bearer '+config.llm_api_key},
                json={'model':'gpt-4o-mini-tts','voice':'coral','input':'Xin chào, tôi muốn trò chuyện.','response_format':'mp3'})
            speech.raise_for_status()
            if not speech.headers.get('content-type','').startswith(('audio/','application/octet-stream')) or not speech.content or len(speech.content)>1_000_000:
                return {**result,'error':'invalid_speech'}
            result['speech']=True
            ai.budget.reserve()
            result['requests_attempted']+=1
            transcript=await client.post(config.llm_base_url+'/audio/transcriptions',
                headers={'Authorization':'Bearer '+config.llm_api_key},
                data={'model':'gpt-4o-mini-transcribe','language':'vi'},
                files={'file':('synthetic.mp3',speech.content,'audio/mpeg')})
            transcript.raise_for_status()
            text=transcript.json().get('text')
            result['transcription']=isinstance(text,str) and len(text.strip())>=5
            if not result['transcription']:
                result['error']='invalid_transcript'
    except HTTPException as exc:
        provider_status=(exc.headers or {}).get('X-CogAI-Provider-Status')
        result['error']='provider_rejected_request' if provider_status else 'daily_limit_or_budget_unavailable'
        result['status_code']=int(provider_status) if provider_status else exc.status_code
    except httpx.HTTPStatusError as exc:
        result['error']='provider_rejected_request'
        result['status_code']=exc.response.status_code
    except ProviderFailure as exc:
        cause=exc.__cause__
        if isinstance(cause,httpx.HTTPStatusError):
            result['error']='provider_rejected_request'
            result['status_code']=cause.response.status_code
        elif isinstance(cause,httpx.HTTPError):
            result['error']='provider_connection_failed'
        else:
            result['error']='provider_reply_invalid'
    except (httpx.HTTPError,ValueError,TypeError):
        result['error']='provider_unavailable_or_invalid_reply'
    return result


if __name__=='__main__':
    try:
        result=asyncio.run(check())
        print(json.dumps(result))
        raise SystemExit(0 if all(result.get(k) for k in ('chat','speech','transcription')) else 1)
    except (ValueError,OSError):
        print('{"error":"configuration_unavailable"}')
        raise SystemExit(1)

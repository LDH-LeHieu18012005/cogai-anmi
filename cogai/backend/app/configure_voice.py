"""Local setup only: secrets enter through getpass, never CLI args or browser."""
import argparse
import getpass
import json
import os
import tempfile
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values, set_key

DEFAULTS={'base_url':'https://api.openai.com/v1','chat_model':'gpt-4.1-mini',
          'transcription_model':'gpt-4o-mini-transcribe','speech_model':'gpt-4o-mini-tts','voice':'coral'}
ENV_FIELDS={'base_url':'COGAI_LLM_BASE_URL','chat_model':'COGAI_LLM_MODEL',
            'transcription_model':'COGAI_TRANSCRIPTION_MODEL','speech_model':'COGAI_SPEECH_MODEL','voice':'COGAI_SPEECH_VOICE'}
ENV_PATH=Path(__file__).resolve().parents[1]/'.env'


def read_secret():
    with warnings.catch_warnings():
        warnings.simplefilter('error',getpass.GetPassWarning)
        try:
            return getpass.getpass('API key (hidden; enter to retain an existing key): ')
        except getpass.GetPassWarning:
            raise ValueError('A terminal with hidden input is required.') from None


def validate(base_url,chat_model,transcription_model,speech_model,voice):
    parts=urlsplit(base_url)
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('Base URL must not contain credentials, query or fragment.')
    if parts.scheme!='https' and not (parts.scheme=='http' and parts.hostname in {'127.0.0.1','localhost','::1'}):
        raise ValueError('Use HTTPS, or HTTP only for a local loopback provider.')
    for value in (chat_model,transcription_model,speech_model,voice):
        if not value or len(value)>256 or any(c in value for c in '\r\n\x00'):
            raise ValueError('Model and voice identifiers must be non-empty single-line values.')


def update(path,values):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    original=path.read_text(encoding='utf-8') if path.exists() else '# Local CogAI configuration. Do not share or commit.\n'
    fd,temp_name=tempfile.mkstemp(prefix='.env.voice.',suffix='.tmp',dir=path.parent)
    temporary=Path(temp_name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as file:
            file.write(original)
        os.chmod(temporary,0o600)
        for key,value in values.items():
            set_key(str(temporary),key,value,quote_mode='always',encoding='utf-8')
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(path,**configuration):
    validate(**configuration)
    choices=dotenv_values(path) if Path(path).exists() else {}
    values={ENV_FIELDS[k]:v for k,v in configuration.items()}
    if 'COGAI_MODE' not in choices:
        values['COGAI_MODE']='demo'
    if 'COGAI_LLM_API_KEY' not in choices:
        values['COGAI_LLM_API_KEY']=''
    update(path,values)


def configure(path,*,key,**configuration):
    validate(**configuration)
    if not key or len(key)>4096 or any(c in key for c in '\r\n\x00'):
        raise ValueError('A non-empty, single-line API key is required.')
    update(path,{**{ENV_FIELDS[k]:v for k,v in configuration.items()},'COGAI_LLM_API_KEY':key,'COGAI_MODE':'live'})


def status(path):
    choices=dotenv_values(path) if Path(path).exists() else {}
    flags={k:bool(choices.get(env)) for k,env in ENV_FIELDS.items()}
    flags['key_configured']=bool(choices.get('COGAI_LLM_API_KEY'))
    flags['live_mode']=choices.get('COGAI_MODE')=='live'
    return {**flags,'ready_to_start':all(flags.values()),'provider_verified':False}


def main():
    parser=argparse.ArgumentParser(description='Configure speech on this machine; never pass API keys as arguments.')
    parser.add_argument('command',choices=['status','prepare','setup'])
    args=parser.parse_args()
    if args.command=='status':
        print(json.dumps(status(ENV_PATH),indent=2));return
    if args.command=='prepare':
        if ENV_PATH.exists():
            print('Existing .env preserved. Use setup to change voice configuration.');return
        prepare(ENV_PATH,**DEFAULTS)
        print('Prepared demo configuration with OpenAI compatibility examples. No key set; no service called.');return
    existing=dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    print('Local voice setup. Nothing is sent to a provider by this command.')
    print('Use model/voice IDs actually offered by your compatible provider.')
    print('OpenAI STT example is a compatibility model; check its deprecation date in the documentation.')
    configuration={}
    for key,env in ENV_FIELDS.items():
        default=existing.get(env) or DEFAULTS[key]
        configuration[key]=input(f'{key} [{default}]: ').strip() or default
    key=read_secret()
    if not key:
        key=existing.get('COGAI_LLM_API_KEY') or ''
    configure(ENV_PATH,key=key,**configuration)
    print('Saved private .env. Restart CogAI, enable voice consent, then start the call.')


if __name__=='__main__':
    try:
        main()
    except (KeyboardInterrupt,EOFError):
        print('\nSetup cancelled.');raise SystemExit(1)
    except (ValueError,OSError):
        print('Configuration could not be saved. Use a terminal supporting hidden input; check endpoint, model/voice IDs and file permissions.');raise SystemExit(1)

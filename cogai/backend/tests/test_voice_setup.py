from pathlib import Path

import pytest
from dotenv import dotenv_values


def test_prepare_preserves_existing_key_and_other_settings(tmp_path):
    from app.configure_voice import prepare
    env=tmp_path/'.env'
    env.write_text('COGAI_LLM_API_KEY="test-key-preserve"\nCOGAI_DATA_DIR="./private-data"\nCOGAI_MODE=demo\n',encoding='utf-8')
    prepare(env,base_url='https://voice.example/v1',chat_model='chat-custom',transcription_model='stt-custom',speech_model='tts-custom',voice='voice-custom')
    values=dotenv_values(env)
    assert values['COGAI_LLM_API_KEY']=='test-key-preserve'
    assert values['COGAI_DATA_DIR']=='./private-data'
    assert values['COGAI_MODE']=='demo'
    assert values['COGAI_SPEECH_MODEL']=='tts-custom'


def test_setup_activates_live_only_with_private_key_and_valid_endpoint(tmp_path):
    from app.configure_voice import configure
    env=tmp_path/'.env'
    with pytest.raises(ValueError):
        configure(env,key='',base_url='https://voice.example/v1',chat_model='c',transcription_model='s',speech_model='t',voice='v')
    assert not env.exists()
    with pytest.raises(ValueError):
        configure(env,key='test-only',base_url='http://outside.example/v1',chat_model='c',transcription_model='s',speech_model='t',voice='v')
    configure(env,key='test-only',base_url='https://voice.example/v1',chat_model='c',transcription_model='s',speech_model='t',voice='v')
    values=dotenv_values(env)
    assert values['COGAI_MODE']=='live' and values['COGAI_LLM_API_KEY']=='test-only'


def test_status_never_returns_key_or_private_endpoint(tmp_path):
    from app.configure_voice import configure,status
    env=tmp_path/'.env'
    configure(env,key='unique-sensitive-test-key',base_url='https://private.example/v1',chat_model='c',transcription_model='s',speech_model='t',voice='v')
    result=status(env)
    assert result['ready_to_start'] is True
    assert 'unique-sensitive-test-key' not in str(result) and 'private.example' not in str(result)


def test_secret_prompt_refuses_echo_fallback(monkeypatch):
    import warnings
    import getpass
    from app.configure_voice import read_secret
    def fallback(*args,**kwargs):
        warnings.warn('Cannot control echo.',getpass.GetPassWarning)
        pytest.fail('An echoed key must never be read')
    monkeypatch.setattr(getpass,'getpass',fallback)
    with pytest.raises(ValueError,match='hidden'):
        read_secret()

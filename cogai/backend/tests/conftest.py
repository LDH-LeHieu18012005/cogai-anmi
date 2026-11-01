"""Software tests must never load the operator's .env or use a real API key."""
import os

from app.config import Settings

Settings.model_config['env_file']=None
os.environ['COGAI_MODE']='demo'
os.environ['COGAI_LLM_API_KEY']=''

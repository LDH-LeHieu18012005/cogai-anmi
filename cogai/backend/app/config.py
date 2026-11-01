from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COGAI_", env_file=".env", extra="ignore")
    mode: Literal["demo", "live"] = "demo"
    environment: Literal["development", "test", "production"] = "development"
    support_accepting: bool = False
    maintenance_seconds: int = 60
    knowledge_development: bool = False
    embedding_model: str = ""
    transcription_model: str = ""
    speech_model: str = ""
    speech_voice: str = ""
    external_daily_call_limit: int = Field(default=0,ge=0,le=100000)
    llm_max_completion_tokens: int = Field(default=1800,ge=128,le=1800)
    research_deep_enabled: bool = True
    voice_max_recording_seconds: int = Field(default=45,ge=2,le=45)
    # Desk devices (xiaozhi firmware) on /xiaozhi/ota/ and /xiaozhi/v1/; off unless enabled.
    device_gateway: bool = False
    # Hosts without persistent disk (Kaggle): "aa:bb:cc:dd:ee:ff=token;..." from a secret, read-only.
    device_tokens: str = Field(default="",repr=False)
    device_timezone_minutes: int = Field(default=420,ge=-720,le=840)
    speech_format: Literal['mp3','wav'] = 'mp3'
    # edge: the single AnMi voice, matching the MYHealth device demo (HoaiMy, default rate).
    # openai uses speech_model/speech_voice instead; the two are never mixed in one deployment.
    # azure: the same HoaiMy voice through the official Azure Speech service (steady latency),
    # falling back to Edge HoaiMy on failure. auto: azure when a key is configured, else edge.
    speech_provider: Literal['openai','edge','azure','auto'] = 'edge'
    edge_voice: str = 'vi-VN-HoaiMyNeural'
    azure_speech_key: str = Field(default="",repr=False)
    azure_speech_region: str = Field(default='southeastasia',pattern=r'^[a-z0-9]{3,30}$')
    edge_rate: str = Field(default='+0%',pattern=r'^[+-]\d{1,2}%$')
    llm_input_usd_per_million: float | None = Field(default=None,ge=0)
    llm_output_usd_per_million: float | None = Field(default=None,ge=0)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = Field(default="",repr=False)
    llm_model: str = "gpt-4.1-mini"
    data_dir: Path = Path("data")
    encryption_key: str = Field(default="",repr=False)
    cookie_secure: bool = False
    allowed_origins: list[str] = [
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1") for port in (5173, 8000, 7860)
    ]
    # Aggregate reports hide any group or bucket smaller than this (brief table 1).
    aggregate_min_group: int = Field(default=5,ge=2,le=1000)
    support_name: str = ""
    support_phone: str = ""
    support_hours: str = ""

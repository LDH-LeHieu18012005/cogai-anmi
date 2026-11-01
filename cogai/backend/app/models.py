from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

Text = Annotated[str, Field(min_length=1, max_length=4000)]
Answer = Annotated[StrictInt, Field(ge=0, le=3)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Consent(InputModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    accepted: Literal[True]
    adult: Literal[True]
    persist: bool = False
    external_ai: bool = False
    version: Literal["2026-10-22.v1"] = "2026-10-22.v1"


class ChatInput(InputModel):
    message: Text
    channel: Literal['text','voice'] = 'text'
    # The browser will read the reply aloud: start speech synthesis as soon as it is checked.
    speak: bool = False
    action: Literal['listen','clarify','identify','evidence','perspective','action'] | None = None
    history: list["Turn"] = Field(default_factory=list, max_length=12)


class Turn(InputModel):
    role: Literal["user", "assistant"]
    content: Annotated[str, Field(min_length=1, max_length=4000)]


class ReframeInput(InputModel):
    situation: Text
    thought: Text
    lenses: list[Literal["CBT", "ACT", "CFT"]] = Field(default=["CBT"], min_length=1, max_length=3)
    previous: Annotated[str, Field(max_length=3000)] = ""
    feedback: Annotated[str, Field(max_length=1000)] = ""


class MoodInput(InputModel):
    score: Annotated[StrictInt, Field(ge=1, le=5)]
    note: Annotated[str, Field(max_length=1000)] = ""


class ScreeningInput(InputModel):
    version: Literal["vi-draft-1"] = "vi-draft-1"
    kind: Literal["PHQ-9", "GAD-7"]
    answers: list[Answer] = Field(min_length=7, max_length=9)
    difficulty: Annotated[StrictInt, Field(ge=0, le=3)] = 0


class FeedbackInput(InputModel):
    record_id: Annotated[str, Field(min_length=1, max_length=64)]
    helpfulness: Annotated[StrictInt, Field(ge=1, le=5)]
    comment: Annotated[str, Field(max_length=1000)] = ""


class Risk(BaseModel):
    level: Literal["low", "check_in", "high", "unavailable"]
    reason: str
    source: Literal["rules", "model", "fallback"]
    requires_support: bool = False
    # Judged with risk in the same model call; safety always takes precedence over scope.
    scope: Literal["in_scope", "off_topic"] = "in_scope"


class Analysis(BaseModel):
    facts: str = Field(max_length=1500)
    interpretation: str = Field(max_length=1500)
    evidence_for: str = Field(max_length=1500)
    evidence_against: str = Field(max_length=1500)
    possible_patterns: list[str] = Field(max_length=5)
    question: str = Field(max_length=1000)


class Candidate(BaseModel):
    lens: Literal["CBT", "ACT", "CFT"]
    reframe: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(max_length=1500)
    next_step: str = Field(max_length=1000)
    review: str = Field(max_length=1000)


class Credentials(InputModel):
    alias: Annotated[str, Field(pattern=r'^[a-z0-9][a-z0-9_-]{2,39}$')]
    password: Annotated[str, Field(min_length=12, max_length=128)]


class ConsentChange(InputModel):
    voice_processing: bool | None = None
    model_config = ConfigDict(extra='forbid', strict=True)
    persist: bool | None = None
    external_ai: bool | None = None
    personalization: bool | None = None
    share_support: bool | None = None
    screening_reminders: bool | None = None


class ReferralInput(InputModel):
    summary: Annotated[str, Field(min_length=1, max_length=3000)]


class CaseUpdate(InputModel):
    status: Literal['accepted','in_progress','resolved','declined','unavailable','out_of_hours']


class ReminderInput(InputModel):
    days: Annotated[StrictInt, Field(ge=7, le=90)]


class RetentionInput(InputModel):
    days: Annotated[StrictInt, Field(ge=1, le=365)]


class SafetyCheckIn(InputModel):
    no_current_danger: Literal[True]
    message: Text


PlanItems = Annotated[list[Annotated[str, Field(min_length=1, max_length=200)]], Field(max_length=6)]


class SafetyPlanInput(InputModel):
    """Stanley & Brown (2012) safety plan, written by the user in their own words."""
    warning_signs: PlanItems = []
    coping: PlanItems = []
    distractions: PlanItems = []
    people: PlanItems = []
    professionals: PlanItems = []
    safe_environment: PlanItems = []
    reasons: PlanItems = []

"""Structured agenda contract shared by parsing, persistence and API responses."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: Text
    owner: Text | None = None
    deadline: date | None = None


class AgendaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: Text
    owner: Text | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    notes: str = Field(default="", max_length=4000)
    action_items: list[ActionItem] = Field(default_factory=list, max_length=30)


class Agenda(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(default="", max_length=2000)
    items: list[AgendaItem] = Field(min_length=1, max_length=30)


class AgendaSave(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agenda: Agenda
    ai_suggestion: Agenda | None = None

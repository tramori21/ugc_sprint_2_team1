from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserActionIn(BaseModel):
    movie_id: str = Field(..., min_length=1, max_length=255)
    event_type: str = Field(..., min_length=1, max_length=50)
    progress_seconds: Optional[int] = Field(default=None, ge=0)
    event_time: Optional[datetime] = None


class UserActionOut(BaseModel):
    status: str
    event_id: str

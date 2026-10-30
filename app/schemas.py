from datetime import datetime
from pydantic import BaseModel, HttpUrl

class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_alias: str | None = None

class ShortenResponse(BaseModel):
    short_code: str
    short_url:str
    original_url: str
    created_at: datetime

class AnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime
    
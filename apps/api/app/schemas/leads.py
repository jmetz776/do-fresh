from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class LeadCreateRequest(BaseModel):
    email: EmailStr
    source: str = "waitlist"
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    profile: Optional[Dict[str, Any]] = None


class LeadOut(BaseModel):
    id: int
    email: str
    source: str
    status: str

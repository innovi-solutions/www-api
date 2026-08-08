from datetime import date as date_type
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

PROJECT_TYPES = (
    "Custom Software",
    "SaaS Application",
    "AI Agents & Automation",
    "Data Engineering",
    "Website",
    "Hosting & Maintenance",
    "Not sure yet",
)

class LeadIn(BaseModel):
    session: Literal["discovery", "technical"]
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    company: str = Field(min_length=1, max_length=150)
    date: date_type
    type: Literal[PROJECT_TYPES]  # only your exact dropdown values pass
    message: str = Field(min_length=10, max_length=2000)
    consent: bool

    # Phase 4 fields — accepted now, enforced later
    website: str = ""            # honeypot
    elapsed_ms: int = 0          # time-to-submit
    turnstile_token: str = ""

    @field_validator("consent")
    @classmethod
    def consent_required(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Consent is required.")
        return v

    @field_validator("date")
    @classmethod
    def date_not_in_past(cls, v: date_type) -> date_type:
        if v < date_type.today():
            raise ValueError("Preferred date cannot be in the past.")
        return v

    @field_validator("name", "company", "message")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class LeadOut(BaseModel):
    ok: bool = True
    message: str = "Request received. We'll be in touch soon."
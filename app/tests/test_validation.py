from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from app.schemas import LeadIn

def valid_payload(**overrides):
    base = {
        "session": "discovery",
        "name": "Test Person",
        "email": "test@example.com",
        "company": "Test Co",
        "date": (date.today() + timedelta(days=7)).isoformat(),
        "type": "Custom Software",
        "message": "We need a booking system for our clinic.",
        "consent": True,
        "website": "",
        "elapsed_ms": 8000,
        "turnstile_token": "tok",
    }
    base.update(overrides)
    return base

def test_valid_payload_parses():
    lead = LeadIn(**valid_payload())
    assert lead.name == "Test Person"

def test_consent_false_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(consent=False))

def test_past_date_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(date="2020-01-01"))

def test_unknown_project_type_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(type="Hacking Services"))

def test_unknown_session_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(session="sales-pitch"))

def test_bad_email_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(email="not-an-email"))

def test_message_too_short_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(message="hi"))

def test_message_too_long_rejected():
    with pytest.raises(ValidationError):
        LeadIn(**valid_payload(message="x" * 2001))

def test_whitespace_stripped():
    lead = LeadIn(**valid_payload(name="  Jane Doe  "))
    assert lead.name == "Jane Doe"
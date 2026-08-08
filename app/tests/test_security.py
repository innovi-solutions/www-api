from types import SimpleNamespace
from app.security.checks import is_honeypot_filled, is_too_fast
from app.services.email import _esc

def test_empty_honeypot_passes():
    assert not is_honeypot_filled(SimpleNamespace(website=""))

def test_filled_honeypot_caught():
    assert is_honeypot_filled(SimpleNamespace(website="http://spam.com"))

def test_whitespace_honeypot_passes():
    assert not is_honeypot_filled(SimpleNamespace(website="   "))

def test_fast_submission_caught():
    assert is_too_fast(SimpleNamespace(elapsed_ms=500))

def test_normal_submission_passes():
    assert not is_too_fast(SimpleNamespace(elapsed_ms=8000))

def test_html_escaping():
    assert _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _esc("Tom & Jerry") == "Tom &amp; Jerry"
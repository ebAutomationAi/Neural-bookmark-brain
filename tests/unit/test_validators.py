# tests/unit/test_validators.py
import pytest
from app.utils.validators import URLValidator, TextValidator

class TestURLValidator:
    def test_valid_url(self):
        is_valid, normalized, error = URLValidator.validate_and_normalize("https://example.com")
        assert is_valid is True
        assert normalized == "https://example.com"
        assert error is None
    
    def test_url_without_scheme(self):
        is_valid, normalized, error = URLValidator.validate_and_normalize("example.com")
        assert is_valid is True
        assert normalized == "https://example.com"
    
    def test_invalid_url(self):
        is_valid, _, error = URLValidator.validate_and_normalize("not a url")
        assert is_valid is False
        assert error is not None
    
    def test_local_url_detection(self):
        domain = URLValidator.extract_domain("http://localhost:8080")
        assert domain == "localhost:8080"

class TestTextValidator:
    def test_clean_text(self):
        dirty = "Text  with\tmultiple\nspaces"
        clean = TextValidator.clean_text(dirty)
        assert clean == "Text with multiple spaces"
    
    def test_truncate(self):
        long_text = "a" * 100
        truncated = TextValidator.truncate(long_text, 50)
        assert len(truncated) == 50
        assert truncated.endswith("...")
    
    def test_meaningful_text(self):
        assert TextValidator.is_meaningful_text("This is a test sentence with enough words", min_words=5)
        assert not TextValidator.is_meaningful_text("Short", min_words=5)
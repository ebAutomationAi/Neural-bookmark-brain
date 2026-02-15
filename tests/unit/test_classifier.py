# tests/unit/test_classifier.py
import pytest
from app.services.classifier import SafetyClassifier

class TestSafetyClassifier:
    @pytest.fixture
    def classifier(self):
        return SafetyClassifier()
    
    def test_nsfw_domain_detection(self, classifier):
        is_nsfw, reason = classifier.classify(
            url="https://pornhub.com/video",
            title="Video",
            text=""
        )
        assert is_nsfw is True
        assert "Dominio NSFW" in reason
    
    def test_nsfw_keyword_in_url(self, classifier):
        is_nsfw, reason = classifier.classify(
            url="https://example.com/adult/content",
            title="Content",
            text=""
        )
        assert is_nsfw is True
        assert "Keyword NSFW en URL" in reason
    
    def test_clean_content(self, classifier):
        is_nsfw, reason = classifier.classify(
            url="https://example.com",
            title="Clean Article",
            text="This is a normal article about technology."
        )
        assert is_nsfw is False
        assert reason is None
    
    def test_keyword_threshold(self, classifier):
        # 1 keyword no debería marcar como NSFW
        is_nsfw, _ = classifier._check_text("This mentions adult once", "test")
        assert is_nsfw is False
        
        # 2+ keywords sí
        is_nsfw, reason = classifier._check_text("This has adult and xxx content", "test")
        assert is_nsfw is True
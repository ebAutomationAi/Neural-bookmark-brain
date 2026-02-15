# tests/unit/test_embeddings.py
import pytest
import numpy as np
from app.services.embeddings import EmbeddingService

class TestEmbeddingService:
    @pytest.fixture
    def service(self):
        return EmbeddingService()
    
    def test_generate_embedding(self, service):
        text = "Machine learning is a subset of artificial intelligence"
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == service.dimension  # 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_empty_text_returns_zero_vector(self, service):
        embedding = service.generate_embedding("")
        assert embedding == [0.0] * service.dimension
    
    def test_similarity_calculation(self, service):
        emb1 = service.generate_embedding("Python programming language")
        emb2 = service.generate_embedding("Python for developers")
        emb3 = service.generate_embedding("Cooking recipes")
        
        sim_similar = service.calculate_similarity(emb1, emb2)
        sim_different = service.calculate_similarity(emb1, emb3)
        
        assert 0 <= sim_similar <= 1
        assert 0 <= sim_different <= 1
        assert sim_similar > sim_different  # Textos similares = mayor score
    
    def test_batch_embeddings(self, service):
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.generate_batch_embeddings(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == service.dimension for emb in embeddings)
# tests/integration/test_agents.py
import pytest
from app.agents import ArchivistAgent, CuratorAgent, AgentOrchestrator

class TestArchivistAgent:
    @pytest.mark.asyncio
    async def test_process_valid_url(self):
        agent = ArchivistAgent()
        result = await agent.process(
            url="https://fastapi.tiangolo.com",
            original_title="FastAPI"
        )
        
        assert result["success"] is True
        assert result["clean_title"] is not None
        assert result["full_text"] is not None
        assert result["is_nsfw"] is False
        assert result["domain"] == "tiangolo.com"
    
    @pytest.mark.asyncio
    async def test_process_local_url(self):
        agent = ArchivistAgent()
        result = await agent.process(
            url="http://localhost:3000",
            original_title="Local App"
        )
        
        assert result["is_local"] is True
        assert "local" in result["error"].lower()

class TestCuratorAgent:
    @pytest.mark.asyncio
    async def test_process_with_valid_text(self):
        agent = CuratorAgent()
        result = await agent.process(
            clean_title="Introduction to Machine Learning",
            full_text="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
            url="https://example.com"
        )
        
        assert result["success"] is True
        assert result["summary"] is not None
        assert len(result["tags"]) > 0
        assert result["category"] is not None
        assert result["embedding"] is not None
        assert len(result["embedding"]) == 384
    
    @pytest.mark.asyncio
    async def test_process_with_insufficient_text(self):
        agent = CuratorAgent()
        result = await agent.process(
            clean_title="Short",
            full_text="Too short",
            url="https://example.com"
        )
        
        # El agente hace fallback url_only cuando texto es insuficiente
        assert "success" in result
        if not result["success"]:
            assert result.get("error") is not None

class TestAgentOrchestrator:
    @pytest.mark.asyncio
    async def test_full_processing_flow(self):
        orchestrator = AgentOrchestrator()
        result = await orchestrator.process_bookmark(
            url="https://www.python.org",
            original_title="Python"
        )
        
        # Verificar que pase por ambos agentes
        assert "clean_title" in result
        assert "summary" in result or result["status"] == "failed"
        assert "processing_time" in result
        assert result["processing_time"] > 0
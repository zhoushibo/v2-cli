# -*- coding: utf-8 -*-
"""
V2 Learning System - Additional Tests for Higher Coverage
Focus on testing parallel_learning and edge cases
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2_learning_system_real.learning_engine import LearningEngine, LearningTask


class TestParallelLearning:
    """Test parallel_learning method - previously untested"""

    @pytest.mark.asyncio
    async def test_parallel_learning_2_perspectives(self):
        """Test parallel learning with 2 perspectives"""
        engine = LearningEngine(num_workers=3)
        
        # Mock LLM provider
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Learning result"
        )
        engine.llm_provider = mock_provider
        
        results = await engine.parallel_learning(
            topic="Python",
            num_perspectives=2,
            save_to_kb=False
        )
        
        assert len(results) == 2
        assert results[0]["perspective"] == "technical"
        assert results[1]["perspective"] == "practical"
        assert all("result" in r for r in results)
        assert all("worker_id" in r for r in results)
        assert all("timestamp" in r for r in results)

    @pytest.mark.asyncio
    async def test_parallel_learning_5_perspectives(self):
        """Test parallel learning with max 5 perspectives"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Result"
        )
        engine.llm_provider = mock_provider
        
        results = await engine.parallel_learning(
            topic="AI",
            num_perspectives=5,
            save_to_kb=False
        )
        
        assert len(results) == 5
        perspectives = [r["perspective"] for r in results]
        assert "technical" in perspectives
        assert "practical" in perspectives
        assert "theoretical" in perspectives
        assert "historical" in perspectives
        assert "comparative" in perspectives

    @pytest.mark.asyncio
    async def test_parallel_learning_with_kb_save(self):
        """Test parallel learning with KB save enabled"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Result"
        )
        engine.llm_provider = mock_provider
        
        # Mock KB integration
        with patch('v2_learning_system_real.knowledge_base_integration_v2.KnowledgeBaseIntegration') as MockKB:
            mock_kb = AsyncMock()
            mock_kb.save_learning_result = AsyncMock(
                return_value={"success": True, "message": "Saved 2 items"}
            )
            MockKB.return_value = mock_kb
            
            results = await engine.parallel_learning(
                topic="ML",
                num_perspectives=2,
                save_to_kb=True
            )
            
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_parallel_learning_kb_save_failure(self):
        """Test parallel learning when KB save fails"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Result"
        )
        engine.llm_provider = mock_provider
        
        with patch('v2_learning_system_real.knowledge_base_integration_v2.KnowledgeBaseIntegration') as MockKB:
            mock_kb = AsyncMock()
            mock_kb.save_learning_result = AsyncMock(
                return_value={"success": False, "error": "KB unavailable"}
            )
            MockKB.return_value = mock_kb
            
            # Should not raise, just print warning
            results = await engine.parallel_learning(
                topic="DL",
                num_perspectives=2,
                save_to_kb=True
            )
            
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_parallel_learning_kb_exception(self):
        """Test parallel learning when KB integration throws exception"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Result"
        )
        engine.llm_provider = mock_provider
        
        with patch('v2_learning_system_real.knowledge_base_integration_v2.KnowledgeBaseIntegration') as MockKB:
            MockKB.side_effect = Exception("Import error")
            
            # Should not raise
            results = await engine.parallel_learning(
                topic="NLP",
                num_perspectives=2,
                save_to_kb=True
            )
            
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_parallel_learning_partial_failure(self):
        """Test parallel learning when some tasks fail"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            side_effect=[
                "Success 1",
                Exception("API Error"),
                "Success 3"
            ]
        )
        engine.llm_provider = mock_provider
        
        results = await engine.parallel_learning(
            topic="Test",
            num_perspectives=3,
            save_to_kb=False
        )
        
        assert len(results) == 3
        assert "Success 1" in results[0]["result"]
        assert "[Failed]" in results[1]["result"]
        assert "Success 3" in results[2]["result"]


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_learning_engine_zero_workers(self):
        """Test engine with 0 workers"""
        engine = LearningEngine(num_workers=0)
        assert engine.num_workers == 0

    def test_learning_engine_negative_workers(self):
        """Test engine with negative workers (should still work)"""
        engine = LearningEngine(num_workers=-1)
        assert engine.num_workers == -1

    @pytest.mark.asyncio
    async def test_execute_task_no_provider_auto_init(self):
        """Test execute_task auto-initializes provider when None"""
        engine = LearningEngine(model="auto-model")
        task = LearningTask(id="t1", topic="Test", worker_id="w0")
        
        with patch('v2_learning_system_real.learning_engine.OpenAIProvider') as MockProvider:
            mock_instance = AsyncMock()
            mock_instance.learning_with_fallback = AsyncMock(
                return_value="Auto-init result"
            )
            MockProvider.return_value = mock_instance
            
            result = await engine.execute_task(task)
            
            MockProvider.assert_called_once_with(model="auto-model")
            assert result == "Auto-init result"
            assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_task_exception_details(self):
        """Test that exception details are captured"""
        engine = LearningEngine()
        
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            side_effect=ValueError("Invalid parameter")
        )
        engine.llm_provider = mock_provider
        
        task = LearningTask(id="t1", topic="Test", worker_id="w0")
        result = await engine.execute_task(task)
        
        assert "[Failed]" in result
        assert task.status == "failed"
        assert task.error == "Invalid parameter"
        assert isinstance(task.duration, float)

    def test_get_task_status_with_all_fields(self):
        """Test get_task_status returns all fields"""
        engine = LearningEngine()
        
        task = LearningTask(
            id="complete-task",
            topic="Complete Test",
            worker_id="worker_99",
            status="completed",
            result="Full result",
            error=None,
            api_calls=2,
            duration=5.5
        )
        engine.tasks["complete-task"] = task
        
        status = engine.get_task_status("complete-task")
        
        assert status["id"] == "complete-task"
        assert status["topic"] == "Complete Test"
        assert status["worker_id"] == "worker_99"
        assert status["status"] == "completed"
        assert status["result"] == "Full result"
        assert status["api_calls"] == 2
        assert status["duration"] == 5.5
        assert "created_at" in status
        assert "completed_at" in status


class TestLearningTaskDataclass:
    """Additional tests for LearningTask dataclass"""

    def test_task_default_values(self):
        """Test all default values in LearningTask"""
        task = LearningTask(
            id="test",
            topic="topic",
            worker_id="worker"
        )
        
        assert task.created_at is not None
        assert task.completed_at is None
        assert task.result is None
        assert task.status == "pending"
        assert task.error is None
        assert task.api_calls == 0
        assert task.duration == 0.0

    def test_task_with_all_parameters(self):
        """Test LearningTask with all parameters set"""
        task = LearningTask(
            id="full-test",
            topic="Full Test",
            worker_id="worker_0",
            created_at=1000000.0,
            completed_at=1005000.0,
            result="Complete",
            status="completed",
            error=None,
            api_calls=3,
            duration=5000.0
        )
        
        assert task.id == "full-test"
        assert task.topic == "Full Test"
        assert task.completed_at == 1005000.0
        assert task.result == "Complete"
        assert task.status == "completed"
        assert task.api_calls == 3
        assert task.duration == 5000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

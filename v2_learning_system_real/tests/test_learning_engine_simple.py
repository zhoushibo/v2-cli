# -*- coding: utf-8 -*-
"""
V2 Learning System - Simple Unit Tests for Learning Engine
Run as: python -m pytest tests/test_learning_engine_simple.py -v
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import asdict

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Now import from package
from v2_learning_system_real.learning_engine import LearningEngine, LearningTask


class TestLearningTask:
    """Test LearningTask dataclass"""

    def test_create_task(self):
        """Test creating a basic learning task"""
        task = LearningTask(
            id="test-123",
            topic="Python Programming",
            worker_id="worker_0"
        )
        
        assert task.id == "test-123"
        assert task.topic == "Python Programming"
        assert task.worker_id == "worker_0"
        assert task.status == "pending"
        assert task.completed_at is None
        assert task.result is None
        assert task.error is None
        assert task.api_calls == 0
        assert task.duration == 0.0
        assert isinstance(task.created_at, float)

    def test_task_to_dict(self):
        """Test converting task to dictionary"""
        task = LearningTask(
            id="test-456",
            topic="Machine Learning",
            worker_id="worker_1",
            status="completed",
            result="ML is awesome",
            api_calls=1,
            duration=2.5
        )
        
        task_dict = asdict(task)
        
        assert task_dict["id"] == "test-456"
        assert task_dict["topic"] == "Machine Learning"
        assert task_dict["status"] == "completed"
        assert task_dict["result"] == "ML is awesome"
        assert task_dict["api_calls"] == 1
        assert task_dict["duration"] == 2.5


class TestLearningEngine:
    """Test LearningEngine class"""

    def test_init_default(self):
        """Test engine initialization with defaults"""
        engine = LearningEngine()
        
        assert engine.num_workers == 3
        assert engine.model is None
        assert engine.llm_provider is None
        assert engine.tasks == {}
        assert engine.running is False

    def test_init_custom(self):
        """Test engine initialization with custom parameters"""
        engine = LearningEngine(num_workers=5, model="glm-4-flash")
        
        assert engine.num_workers == 5
        assert engine.model == "glm-4-flash"
        assert engine.llm_provider is None

    @pytest.mark.asyncio
    async def test_submit_learning_task(self):
        """Test submitting a learning task"""
        engine = LearningEngine()
        
        task = await engine.submit_learning_task(
            topic="Deep Learning",
            worker_id="worker_0"
        )
        
        assert task.id is not None
        assert task.topic == "Deep Learning"
        assert task.worker_id == "worker_0"
        assert task.status == "pending"
        assert task.id in engine.tasks

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution"""
        engine = LearningEngine()
        
        # Mock LLM provider
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            return_value="Deep learning is a subset of ML"
        )
        engine.llm_provider = mock_provider
        
        task = LearningTask(
            id="test-exec",
            topic="Deep Learning",
            worker_id="worker_0"
        )
        
        result = await engine.execute_task(
            task,
            perspective="technical",
            style="detailed"
        )
        
        assert result == "Deep learning is a subset of ML"
        assert task.status == "completed"
        assert task.result == "Deep learning is a subset of ML"
        assert task.api_calls == 1
        assert task.duration >= 0  # Duration can be 0 for fast operations
        assert task.completed_at is not None
        mock_provider.learning_with_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test task execution with failure"""
        engine = LearningEngine()
        
        # Mock LLM provider to raise exception
        mock_provider = AsyncMock()
        mock_provider.learning_with_fallback = AsyncMock(
            side_effect=Exception("API Error")
        )
        engine.llm_provider = mock_provider
        
        task = LearningTask(
            id="test-fail",
            topic="Deep Learning",
            worker_id="worker_0"
        )
        
        result = await engine.execute_task(task)
        
        assert "[Failed]" in result
        assert task.status == "failed"
        assert task.error == "API Error"

    @pytest.mark.asyncio
    async def test_execute_task_auto_init_provider(self):
        """Test that engine auto-initializes LLM provider"""
        engine = LearningEngine(model="test-model")
        
        task = LearningTask(
            id="test-auto",
            topic="Test",
            worker_id="worker_0"
        )
        
        with patch('v2_learning_system_real.learning_engine.OpenAIProvider') as MockProvider:
            mock_instance = AsyncMock()
            mock_instance.learning_with_fallback = AsyncMock(
                return_value="Test result"
            )
            MockProvider.return_value = mock_instance
            
            result = await engine.execute_task(task)
            
            MockProvider.assert_called_once_with(model="test-model")
            assert result == "Test result"

    def test_get_task_status(self):
        """Test getting task status"""
        engine = LearningEngine()
        
        task = LearningTask(
            id="status-test",
            topic="Test",
            worker_id="worker_0",
            status="completed"
        )
        engine.tasks["status-test"] = task
        
        status = engine.get_task_status("status-test")
        
        assert status is not None
        assert status["id"] == "status-test"
        assert status["status"] == "completed"

    def test_get_task_status_not_found(self):
        """Test getting non-existent task status"""
        engine = LearningEngine()
        
        status = engine.get_task_status("non-existent")
        
        assert status is None

    def test_get_all_tasks(self):
        """Test getting all tasks"""
        engine = LearningEngine()
        
        task1 = LearningTask(id="t1", topic="Topic 1", worker_id="w0")
        task2 = LearningTask(id="t2", topic="Topic 2", worker_id="w1")
        
        engine.tasks["t1"] = task1
        engine.tasks["t2"] = task2
        
        all_tasks = engine.get_all_tasks()
        
        assert len(all_tasks) == 2
        assert all_tasks[0]["id"] in ["t1", "t2"]
        assert all_tasks[1]["id"] in ["t1", "t2"]

    def test_get_all_tasks_empty(self):
        """Test getting all tasks when empty"""
        engine = LearningEngine()
        
        all_tasks = engine.get_all_tasks()
        
        assert all_tasks == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

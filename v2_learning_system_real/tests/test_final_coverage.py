# -*- coding: utf-8 -*-
"""
V2 Learning System - Final Coverage Tests
Target: Cover remaining lines to reach 80%+
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO

# Setup path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from v2_learning_system_real.learning_engine import LearningEngine, LearningTask


class TestMainFunction:
    """Test the main() function - lines 144-165"""

    @pytest.mark.asyncio
    async def test_main_function(self, capsys):
        """Test the main test function in learning_engine"""
        from v2_learning_system_real import learning_engine
        
        # Mock parallel_learning to avoid actual API calls
        with patch.object(LearningEngine, 'parallel_learning', new_callable=AsyncMock) as mock_parallel:
            mock_parallel.return_value = [
                {"perspective": "technical", "result": "Tech result" * 20},
                {"perspective": "practical", "result": "Prac result"}
            ]
            
            # Run main function
            await learning_engine.main()
            
            # Capture output
            captured = capsys.readouterr()
            
            # Verify output contains expected text
            assert "V2 Learning Engine Test" in captured.out
            assert "Testing parallel learning..." in captured.out
            assert "Learning completed!" in captured.out
            assert "Results: 2 perspectives" in captured.out
            assert "Test completed successfully!" in captured.out
            
            # Verify parallel_learning was called
            mock_parallel.assert_called_once()


class TestKnowledgeBaseIntegrationSave:
    """Test KB integration save with auto_generate_embedding=False"""

    @pytest.mark.asyncio
    async def test_save_without_embedding(self):
        """Test save_learning_result with auto_generate_embedding=False"""
        from v2_learning_system_real.knowledge_base_integration_v2 import KnowledgeBaseIntegration
        
        kb = KnowledgeBaseIntegration()
        kb.initialized = True
        
        # Mock KB components
        mock_ingest = Mock()
        kb.KnowledgeIngest = Mock(return_value=mock_ingest)
        
        mock_embedding = Mock()
        kb.EmbeddingGenerator = Mock(return_value=mock_embedding)
        
        mock_index = Mock()
        mock_index.add_documents = Mock(return_value=3)
        kb.KnowledgeIndex = Mock(return_value=mock_index)
        
        mock_fts = Mock()
        mock_fts.add_documents = Mock(return_value=3)
        mock_fts.close = Mock()
        kb.KnowledgeSearchFTS = Mock(return_value=mock_fts)
        
        # Mock Path
        with patch('v2_learning_system_real.knowledge_base_integration_v2.Path') as MockPath:
            mock_path = Mock()
            mock_path.exists = Mock(return_value=True)
            mock_path.mkdir = Mock()
            MockPath.return_value = mock_path
            
            result = await kb.save_learning_result(
                topic="Test No Embedding",
                learning_data=[
                    {"perspective": "test", "result": "Result", "timestamp": "2026-02-19"}
                ],
                source="test",
                auto_generate_embedding=False  # Test this parameter
            )
            
            assert result["success"] is True
            assert result["topic"] == "Test No Embedding"


class TestSearchKnowledge:
    """Test search_knowledge method"""

    def test_search_knowledge_basic(self):
        """Test basic knowledge search"""
        from v2_learning_system_real.knowledge_base_integration_v2 import KnowledgeBaseIntegration
        
        kb = KnowledgeBaseIntegration()
        kb.initialized = True
        kb.kb_path = Path("/fake/path")
        
        # Mock FTS
        mock_fts = Mock()
        mock_fts.search = Mock(return_value=[
            {"title": "Result 1", "content": "...", "rowid": 1},
            {"title": "Result 2", "content": "...", "rowid": 2}
        ])
        mock_fts.close = Mock()
        
        with patch('v2_learning_system_real.knowledge_base_integration_v2.KnowledgeSearchFTS', return_value=mock_fts):
            results = kb.search_knowledge("Python", limit=5)
            
            assert len(results) == 2
            assert results[0]["title"] == "Result 1"
            mock_fts.search.assert_called_once_with(query="Python", limit=5, highlight=True)
            mock_fts.close.assert_called_once()

    def test_search_knowledge_error(self, caplog):
        """Test search with error"""
        from v2_learning_system_real.knowledge_base_integration_v2 import KnowledgeBaseIntegration
        
        kb = KnowledgeBaseIntegration()
        kb.initialized = True
        kb.kb_path = Path("/fake/path")
        
        with patch('v2_learning_system_real.knowledge_base_integration_v2.KnowledgeSearchFTS', side_effect=Exception("Search failed")):
            results = kb.search_knowledge("Python")
            
            assert results == []


class TestPrepareKnowledgeItemsEdgeCases:
    """Test _prepare_knowledge_items edge cases"""

    def test_prepare_with_missing_fields(self):
        """Test preparing items with missing optional fields"""
        from v2_learning_system_real.knowledge_base_integration_v2 import KnowledgeBaseIntegration
        
        kb = KnowledgeBaseIntegration()
        kb.initialized = True
        
        learning_data = [
            {
                "perspective": "technical",
                "result": "Result"
                # Missing timestamp
            }
        ]
        
        items = kb._prepare_knowledge_items(
            topic="Test",
            learning_data=learning_data,
            source="test"
        )
        
        assert len(items) == 1
        assert "metadata" in items[0]
        assert items[0]["metadata"]["topic"] == "Test"
        assert items[0]["metadata"]["perspective"] == "technical"

    def test_prepare_empty_learning_data(self):
        """Test preparing with empty learning data"""
        from v2_learning_system_real.knowledge_base_integration_v2 import KnowledgeBaseIntegration
        
        kb = KnowledgeBaseIntegration()
        kb.initialized = True
        
        items = kb._prepare_knowledge_items(
            topic="Test",
            learning_data=[],
            source="test"
        )
        
        assert len(items) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# -*- coding: utf-8 -*-
"""
V2 Learning System - Knowledge Base Integration Module
Auto-save learning results to knowledge base
Supports auto-deduplication and update (v2.0)
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeBaseIntegration:
    """Knowledge Base Integrator with auto-deduplication"""
    
    def __init__(self, knowledge_base_path: str = None):
        if knowledge_base_path is None:
            current_path = Path(__file__).parent
            workspace_path = current_path.parent
            kb_path = workspace_path / "knowledge_base"
            if not kb_path.exists():
                logger.warning(f"Knowledge base path not found: {kb_path}")
                kb_path = None
            else:
                kb_path = Path(knowledge_base_path)
        self.kb_path = kb_path
        self.initialized = False
        self.KnowledgeIngest = None
        self.KnowledgeIndex = None
        self.EmbeddingGenerator = None
        self.KnowledgeSearchFTS = None

    def _ensure_initialized(self):
        if self.initialized:
            return
        if not self.kb_path:
            raise RuntimeError("Knowledge base path not configured")
        
        kb_path_str = str(self.kb_path)
        if kb_path_str not in sys.path:
            sys.path.insert(0, kb_path_str)
        
        try:
            from core import KnowledgeIngest, KnowledgeIndex, EmbeddingGenerator
            from core.knowledge_search_fts import KnowledgeSearchFTS
            self.KnowledgeIngest = KnowledgeIngest
            self.KnowledgeIndex = KnowledgeIndex
            self.EmbeddingGenerator = EmbeddingGenerator
            self.KnowledgeSearchFTS = KnowledgeSearchFTS
            self.initialized = True
            logger.info(f"[OK] Knowledge base integration initialized: {self.kb_path}")
        except ImportError as e:
            logger.error(f"[FAIL] Failed to import knowledge base modules: {e}")
            raise RuntimeError(f"Cannot import knowledge base modules: {e}")

    async def save_learning_result(
        self,
        topic: str,
        learning_data: List[Dict[str, Any]],
        source: str = "v2_learning_system",
        auto_generate_embedding: bool = True,
        update_existing: bool = True
    ) -> Dict[str, Any]:
        self._ensure_initialized()
        try:
            knowledge_items = self._prepare_knowledge_items(topic, learning_data, source)
            
            data_path = self.kb_path / "data"
            data_path.mkdir(exist_ok=True)
            
            ingest = self.KnowledgeIngest(max_file_size_mb=50)
            embedding_gen = self.EmbeddingGenerator(
                cache_path=str(data_path / "embedding_cache.json")
            )
            index = self.KnowledgeIndex(
                chroma_path=str(data_path / "chromadb"),
                embedding_generator=embedding_gen
            )
            fts = self.KnowledgeSearchFTS(db_path=str(data_path / "knowledge_fts.db"))
            
            stats = {"new": 0, "updated": 0, "skipped": 0}
            
            if update_existing:
                logger.info(f"[UPDATE] Checking for existing knowledge (topic: {topic})...")
                knowledge_items = self._deduplicate_items(index, fts, knowledge_items, stats)
                logger.info(f"[UPDATE] Deduplication complete: new={stats['new']}, updated={stats['updated']}, skipped={stats['skipped']}")
            
            if len(knowledge_items) == 0:
                return {
                    "success": True,
                    "topic": topic,
                    "knowledge_items": 0,
                    "chroma_count": 0,
                    "fts_count": 0,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat(),
                    "message": "[OK] Knowledge is up to date, no update needed"
                }
            
            logger.info(f"[SAVE] Saving {len(knowledge_items)} items to ChromaDB...")
            chroma_count = index.add_documents(knowledge_items, auto_generate=auto_generate_embedding)
            
            logger.info(f"[SAVE] Saving {len(knowledge_items)} items to FTS5...")
            fts_docs = [
                {
                    "content": item["content"],
                    "title": item.get("metadata", {}).get("title", ""),
                    "tags": item.get("metadata", {}).get("tags", ""),
                    "source": item.get("metadata", {}).get("source", ""),
                    "metadata": item.get("metadata", {})
                }
                for item in knowledge_items
            ]
            fts_count = fts.add_documents(fts_docs)
            fts.close()
            
            total_count = stats['new'] + stats['updated']
            result = {
                "success": True,
                "topic": topic,
                "knowledge_items": total_count,
                "chroma_count": chroma_count,
                "fts_count": fts_count,
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
                "message": f"[OK] Saved: {stats['new']} new, {stats['updated']} updated"
            }
            logger.info(result["message"])
            return result
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to save learning result: {e}")
            return {
                "success": False,
                "topic": topic,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "message": f"[FAIL] Save failed: {str(e)}"
            }

    def _deduplicate_items(
        self,
        index: Any,
        fts: Any,
        knowledge_items: List[Dict],
        stats: Dict[str, int]
    ) -> List[Dict]:
        items_to_add = []
        
        for item in knowledge_items:
            metadata = item.get("metadata", {})
            topic = metadata.get("topic", "")
            perspective = metadata.get("perspective", "")
            title = metadata.get("title", "")
            
            existing = self._find_existing_fts(fts, topic, perspective)
            
            if existing:
                logger.info(f"[UPDATE] Found existing knowledge: {title}")
                
                old_id = existing.get('id')
                if old_id:
                    try:
                        index.collection.delete(ids=[old_id])
                        logger.info(f"[UPDATE] Deleted old entry from ChromaDB: {old_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete from ChromaDB: {e}")
                
                try:
                    cursor = fts.conn.cursor()
                    cursor.execute(
                        "DELETE FROM knowledge_fts WHERE rowid = ?",
                        (existing.get('rowid'),)
                    )
                    fts.conn.commit()
                    logger.info(f"[UPDATE] Deleted old entry from FTS5: {existing.get('rowid')}")
                except Exception as e:
                    logger.warning(f"Failed to delete from FTS5: {e}")
                
                items_to_add.append(item)
                stats['updated'] += 1
            else:
                items_to_add.append(item)
                stats['new'] += 1
        
        return items_to_add

    def _find_existing_fts(self, fts: Any, topic: str, perspective: str) -> Optional[Dict]:
        query = f"{topic} {perspective}"
        results = fts.search(query=query, limit=20)
        
        for result in results:
            title = result.get('title', '')
            if topic in title and perspective in title:
                return {
                    'rowid': result.get('rowid'),
                    'id': f"doc_{result.get('rowid', 0)}",
                    'title': title,
                    'content': result.get('content', '')
                }
        
        return None

    def _prepare_knowledge_items(
        self,
        topic: str,
        learning_data: List[Dict[str, Any]],
        source: str
    ) -> List[Dict]:
        knowledge_items = []
        for i, data in enumerate(learning_data):
            perspective = data.get("perspective", "unknown")
            result = data.get("result", "")
            timestamp = data.get("timestamp", "")
            
            content = f"""# {topic}
## Perspective {i+1}: {perspective.capitalize()}

{result}

---
*Learning time: {timestamp}*
*Source: {source}*
"""
            
            metadata = {
                "title": f"{topic} - {perspective} Perspective",
                "tags": f"{topic},{perspective},v2_learning",
                "source": source,
                "topic": topic,
                "perspective": perspective,
                "learning_time": timestamp,
                "item_index": i + 1,
                "total_items": len(learning_data)
            }
            
            knowledge_items.append({
                "content": content,
                "metadata": metadata
            })
        
        logger.info(f"Prepared {len(knowledge_items)} knowledge items")
        return knowledge_items

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict]:
        self._ensure_initialized()
        try:
            fts = self.KnowledgeSearchFTS(db_path=str(self.kb_path / "data" / "knowledge_fts.db"))
            results = fts.search(query=query, limit=limit, highlight=True)
            fts.close()
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


if __name__ == "__main__":
    async def test():
        print("=" * 80)
        print("TEST: Auto-deduplication and Update")
        print("=" * 80)
        
        kb = KnowledgeBaseIntegration()
        
        topic = "Test Topic"
        data_v1 = [{"perspective": "technical", "result": "Content v1", "timestamp": "2026-02-19T00:00:00"}]
        
        print(f"\n[Test 1] First learning: {topic}")
        result1 = await kb.save_learning_result(topic, data_v1)
        print(f"Result: {result1['message']}")
        
        data_v2 = [{"perspective": "technical", "result": "Content v2 (UPDATED)", "timestamp": "2026-02-19T00:30:00"}]
        
        print(f"\n[Test 2] Second learning (update): {topic}")
        result2 = await kb.save_learning_result(topic, data_v2)
        print(f"Result: {result2['message']}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETED")
        print("=" * 80)
    
    asyncio.run(test())

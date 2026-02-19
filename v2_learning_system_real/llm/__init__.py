# -*- coding: utf-8 -*-
"""LLM Provider Module - Mock for testing"""

class APIError(Exception):
    """API Error exception"""
    pass

class LLMProvider:
    """Base LLM Provider class"""
    def __init__(self, model=None):
        self.model = model
    
    async def learning_with_fallback(self, topic, perspective="technical", style="detailed"):
        """Learn with fallback mechanism"""
        raise NotImplementedError()

class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (works with NVIDIA, Zhipu, etc.)"""
    def __init__(self, model=None):
        super().__init__(model=model)
    
    async def learning_with_fallback(self, topic, perspective="technical", style="detailed"):
        """
        Learn about a topic with fallback to alternative providers
        
        Args:
            topic: Learning topic
            perspective: Learning perspective (technical, practical, etc.)
            style: Response style (detailed, concise, etc.)
        
        Returns:
            Learning result string
        """
        # This is a mock implementation for testing
        # Real implementation would call actual LLM APIs
        return f"Learning result for '{topic}' from {perspective} perspective"

class HTTPProvider(LLMProvider):
    """HTTP-based LLM provider"""
    def __init__(self, base_url=None, model=None):
        super().__init__(model=model)
        self.base_url = base_url
    
    async def learning_with_fallback(self, topic, perspective="technical", style="detailed"):
        """Learn via HTTP"""
        return f"HTTP learning result for '{topic}'"

"""
Abee LLM Client - ARES 双脑副脑大模型客户端

遵守规则 7：仅使用 HTTP API 通信（禁止 WinRS）

@author Claw
@since 2026-02-23
"""

import requests
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    """模型来源"""
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: ModelType
    param_size: str  # "30B", "397B"
    quantization: str  # "Q4_K_M"


@dataclass
class ChatMessage:
    """对话消息"""
    role: str  # "system", "user", "assistant"
    content: str


class AbeeLLMClient:
    """
    abee 大模型客户端

    支持两个来源：
    1. LM Studio (端口 1234)
    2. Ollama (端口 11434)
    """

    def __init__(self, base_url: str, provider: ModelType = ModelType.LM_STUDIO, timeout: int = 30):
        """
        初始化客户端

        Args:
            base_url: API 基础地址
            provider: 模型来源（LM_STUDIO 或 OLLAMA）
            timeout: 请求超时（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.provider = provider
        self.timeout = timeout
        self.session = requests.Session()

        # 设置默认 headers
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def list_models(self) -> List[ModelInfo]:
        """
        获取可用模型列表

        Returns:
            模型信息列表
        """
        if self.provider == ModelType.LM_STUDIO:
            url = f"{self.base_url}/v1/models"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            models = []
            for model in data['data']:
                models.append(ModelInfo(
                    id=model['id'],
                    name=model['id'],
                    provider=ModelType.LM_STUDIO,
                    param_size=self._extract_param_size(model['id']),
                    quantization="N/A"
                ))
            return models

        elif self.provider == ModelType.OLLAMA:
            url = f"{self.base_url}/api/tags"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            models = []
            for model in data['models']:
                details = model.get('details', {})
                models.append(ModelInfo(
                    id=model['name'],
                    name=model['name'],
                    provider=ModelType.OLLAMA,
                    param_size=details.get('parameter_size', 'N/A'),
                    quantization=details.get('quantization_level', 'N/A')
                ))
            return models

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def chat_completions(
        self,
        model: str,
        messages: List[ChatMessage],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        聊天完成（OpenAI 兼容 API）

        Args:
            model: 模型 ID
            messages: 对话消息列表
            max_tokens: 最大生成 token 数
            temperature: 温度参数（0-1）
            stream: 是否流式输出

        Returns:
            API 响应
        """
        if self.provider == ModelType.LM_STUDIO:
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }

            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        elif self.provider == ModelType.OLLAMA:
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }

            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否可用
        """
        try:
            if self.provider == ModelType.LM_STUDIO:
                url = f"{self.base_url}/v1/models"
            else:
                url = f"{self.base_url}/api/tags"

            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[AbeeLLMClient] Health check failed: {e}")
            return False

    def _extract_param_size(self, model_id: str) -> str:
        """
        从模型 ID 提取参数大小

        Args:
            model_id: 模型 ID

        Returns:
            参数大小（如 "30B", "397B"）
        """
        if "30b" in model_id.lower() or "30-b" in model_id.lower():
            return "30B"
        elif "397b" in model_id.lower() or "397-b" in model_id.lower():
            return "397B"
        elif "32b" in model_id.lower() or "32-b" in model_id.lower():
            return "32B"
        elif "7b" in model_id.lower() or "7-b" in model_id.lower():
            return "7B"
        else:
            return "N/A"


# ============ 单例管理 ============

_lm_studio_client: Optional[AbeeLLMClient] = None
_ollama_client: Optional[AbeeLLMClient] = None


def get_lm_studio_client() -> AbeeLLMClient:
    """获取 LM Studio 客户端单例"""
    global _lm_studio_client
    if _lm_studio_client is None:
        _lm_studio_client = AbeeLLMClient(
            base_url="http://192.168.3.200:1234",
            provider=ModelType.LM_STUDIO,
            timeout=60,  # LM Studio 首次加载可能需要较长时间
        )
    return _lm_studio_client


def get_ollama_client() -> AbeeLLMClient:
    """获取 Ollama 客户端单例"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = AbeeLLMClient(
            base_url="http://192.168.3.200:11434",
            provider=ModelType.OLLAMA,
            timeout=60,
        )
    return _ollama_client


# ============ 便捷函数 ============

def chat_with_model(
    model_id: str,
    user_message: str,
    provider: ModelType = ModelType.LM_STUDIO,
) -> str:
    """
    便捷的聊天函数

    Args:
        model_id: 模型 ID
        user_message: 用户消息
        provider: 模型来源

    Returns:
        模型响应
    """
    if provider == ModelType.LM_STUDIO:
        client = get_lm_studio_client()
    else:
        client = get_ollama_client()

    messages = [
        ChatMessage(role="user", content=user_message),
    ]

    response = client.chat_completions(
        model=model_id,
        messages=messages,
        max_tokens=256,
        temperature=0.7,
    )

    return response['choices'][0]['message']['content']


# ============ 测试代码 ============

if __name__ == "__main__":
    import time

    print("=" * 60)
    print("Abee LLM Client Test")
    print("=" * 60)

    # Test LM Studio
    print("\n[1] Test LM Studio")
    lm_client = get_lm_studio_client()

    print("  Health check...")
    is_healthy = lm_client.health_check()
    print(f"  Status: {'OK' if is_healthy else 'FAILED'}")

    if is_healthy:
        print("  Get model list...")
        models = lm_client.list_models()
        print(f"  Available models: {len(models)}")
        for model in models:
            print(f"    - {model.name} ({model.param_size}, {model.quantization})")

        print("\n  Test qwen3-coder-30b...")
        try:
            start = time.time()
            response = lm_client.chat_completions(
                model="qwen3-coder-30b-a3b-instruct",
                messages=[ChatMessage(role="user", content="Hello, who are you?")],
                max_tokens=100,
            )
            duration = time.time() - start
            content = response['choices'][0]['message']['content']
            print(f"  Latency: {duration:.2f}s")
            print(f"  Response: {content}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Test Ollama
    print("\n[2] Test Ollama")
    ollama_client = get_ollama_client()

    print("  Health check...")
    is_healthy = ollama_client.health_check()
    print(f"  Status: {'OK' if is_healthy else 'FAILED'}")

    if is_healthy:
        print("  Get model list...")
        models = ollama_client.list_models()
        print(f"  Available models: {len(models)}")
        for model in models:
            print(f"    - {model.name} ({model.param_size}, {model.quantization})")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

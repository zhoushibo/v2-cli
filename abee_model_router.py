"""
Abee Model Router - abee 智能模型路由器

功能：
1. 自动选择最优模型
2. 降级策略（大模型不可用时降级到小模型）
3. 健康检查 + 自动切换

遵守规则 7：仅使用 HTTP API 通信

@author Claw
@since 2026-02-23
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import requests
import time


class TaskType(Enum):
    """任务类型"""
    # 实时任务：需要快速响应
    REALTIME = "realtime"
    # 推理任务：需要深度思考
    REASONING = "reasoning"
    # 编码任务：需要代码生成
    CODING = "coding"
    # 生成任务：需要高质量输出
    GENERATION = "generation"


class ModelTier(Enum):
    """模型层级"""
    # L5: 超大模型（397B），深度推理
    L5_SUPER_LARGE = "L5"
    # L4: 大模型（32B），复杂任务
    L4_LARGE = "L4"
    # L3: 中等模型（30B），日常任务
    L3_MEDIUM = "L3"
    # L2: 小模型（7B），快速响应
    L2_SMALL = "L2"
    # L1: 超小模型，极速响应
    L1_TINY = "L1"


@dataclass
class ModelConfig:
    """模型配置"""
    id: str
    name: str
    provider: str  # "lm_studio" or "ollama"
    tier: ModelTier
    param_size: str  # "7B", "30B", "397B"
    latency_ms: int  # 平均延迟（毫秒）
    max_tokens: int
    context_window: int


class AbeeModelRouter:
    """
    abee 智能模型路由器

    模型清单：
    ============ LM Studio (端口 1234) ============
    - qwen2-7b-instruct: L2_SMALL, ~1s, 7B
    - qwen3-coder-30b: L3_MEDIUM, ~2.3s, 30B (可能被 397B 占用显存)
    - qwen3.5-397b: L5_SUPER_LARGE, ~15s, 397B (推理模式硬编码)

    ============ Ollama (端口 11434) ============
    - qwen2.5-coder:32b: L4_LARGE, ~19.6s, 32B
    - deepseek-r1:32b: L4_LARGE, ~21.6s, 32B
    """

    def __init__(self):
        """初始化路由器"""
        # 模型清单（按性能排序：实测 tokens/s）
        self.models = [
            # L3: 中等模型（最优：82.0 tokens/s，实测最快）
            ModelConfig(
                id="qwen3-coder-30b-a3b-instruct",
                name="Qwen3-Coder-30B",
                provider="lm_studio",
                tier=ModelTier.L3_MEDIUM,
                param_size="30B",
                latency_ms=1550,  # 实测 1.55s
                max_tokens=8192,
                context_window=131072,
            ),

            # L2: 小模型（快速：47.7 tokens/s）
            ModelConfig(
                id="qwen2-7b-instruct",
                name="Qwen2-7B-Instruct",
                provider="lm_studio",
                tier=ModelTier.L2_SMALL,
                param_size="7B",
                latency_ms=3430,  # 实测 3.43s
                max_tokens=2048,
                context_window=32768,
            ),

            # L4: 大模型（备用：13.9 tokens/s，10s+）
            ModelConfig(
                id="qwen2.5-coder:32b",
                name="Qwen2.5-Coder-32B",
                provider="ollama",
                tier=ModelTier.L4_LARGE,
                param_size="32B",
                latency_ms=10660,  # 实测 10.66s
                max_tokens=4096,
                context_window=32768,
            ),
            ModelConfig(
                id="deepseek-r1:32b",
                name="DeepSeek-R1-32B",
                provider="ollama",
                tier=ModelTier.L4_LARGE,
                param_size="32B",
                latency_ms=21600,  # 之前实测 21.6s
                max_tokens=4096,
                context_window=32768,
            ),

            # L5: 超大模型（深度推理：已卸载，预留）
            ModelConfig(
                id="qwen3.5-397b-a17b",
                name="Qwen3.5-397B",
                provider="lm_studio",
                tier=ModelTier.L5_SUPER_LARGE,
                param_size="397B",
                latency_ms=15000,
                max_tokens=8192,
                context_window=131072,
            ),
        ]

        # 模型健康状态缓存
        self.model_health: Dict[str, bool] = {}

        # 默认超时（健康检查用更短的超时，避免阻塞）
        self.health_check_timeout = 30  # 健康检查超时从 10s 增加到 30s
        self.default_timeout = 60

    def route(
        self,
        task_type: TaskType = TaskType.REALTIME,
        prefer_tier: Optional[ModelTier] = None,
    ) -> ModelConfig:
        """
        智能路由：根据任务类型选择最优模型

        Args:
            task_type: 任务类型
            prefer_tier: 强制指定层级（可选）

        Returns:
            最优模型配置
        """
        # 如果指定了层级，优先选择
        if prefer_tier:
            candidates = [m for m in self.models if m.tier == prefer_tier]
            if candidates:
                return self._select_healthy(candidates)

        # 根据任务类型自动选择
        if task_type == TaskType.REALTIME:
            # 实时任务：优先 L2（快速响应）
            return self._select_healthy(self.models)

        elif task_type == TaskType.REASONING:
            # 推理任务：优先 L4/L5（深度思考）
            reasoning_models = [m for m in self.models if m.tier in [ModelTier.L4_LARGE, ModelTier.L5_SUPER_LARGE]]
            return self._select_healthy(reasoning_models if reasoning_models else self.models)

        elif task_type == TaskType.CODING:
            # 编码任务：优先 L3（最快 coder）
            return self._select_healthy(self.models)

        elif task_type == TaskType.GENERATION:
            # 生成任务：优先 L3（最快 82 tokens/s）
            return self._select_healthy(self.models)

        else:
            # 默认：L2/L3（平衡）
            return self._select_healthy(self.models)

    def _select_healthy(self, candidates: List[ModelConfig]) -> ModelConfig:
        """
        从候选模型中选择健康的

        Args:
            candidates: 候选模型列表

        Returns:
            健康的模型配置
        """
        for model in candidates:
            if self._check_health(model):
                return model

        # 所有候选都不健康，降级到最后一个
        print(f"[Router] All candidates unhealthy, falling back to: {candidates[-1].name}")
        return candidates[-1]

    def _check_health(self, model: ModelConfig) -> bool:
        """
        检查模型健康状态（带缓存）

        Args:
            model: 模型配置

        Returns:
            是否健康
        """
        model_id = model.id

        # 检查缓存（缓存 60 秒）
        if model_id in self.model_health:
            cached_time, is_healthy = self.model_health[model_id]
            if time.time() - cached_time < 60:
                return is_healthy

        # 实际检查
        is_healthy = self._health_check(model)

        # 更新缓存
        self.model_health[model_id] = (time.time(), is_healthy)

        if not is_healthy:
            print(f"[Router] Model unhealthy: {model.name} ({model.id})")

        return is_healthy

    def _health_check(self, model: ModelConfig) -> bool:
        """
        健康检查（实际调用 API）

        Args:
            model: 模型配置

        Returns:
            是否健康
        """
        if model.provider == "lm_studio":
            url = f"http://192.168.3.200:1234/v1/chat/completions"
        else:  # ollama
            url = f"http://192.168.3.200:11434/v1/chat/completions"

        payload = {
            "model": model.id,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
        }

        try:
            r = requests.post(url, json=payload, timeout=self.health_check_timeout)
            # 200 = 成功, 400 = 模型加载失败
            return r.status_code == 200
        except Exception as e:
            print(f"[Router] Health check error: {e}")
            return False

    def get_model_by_id(self, model_id: str) -> Optional[ModelConfig]:
        """
        根据 ID 获取模型配置

        Args:
            model_id: 模型 ID

        Returns:
            模型配置（不存在则返回 None）
        """
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def list_available_models(self, tier: Optional[ModelTier] = None) -> List[ModelConfig]:
        """
        列出可用模型

        Args:
            tier: 可选，筛选层级

        Returns:
            可用模型列表
        """
        if tier:
            return [m for m in self.models if m.tier == tier]
        else:
            return self.models.copy()


# ============ 便捷函数 ============

_router_instance: Optional[AbeeModelRouter] = None


def get_router() -> AbeeModelRouter:
    """获取路由器单例"""
    global _router_instance
    if _router_instance is None:
        _router_instance = AbeeModelRouter()
    return _router_instance


def route_for_task(
    task_type: TaskType = TaskType.REALTIME,
) -> ModelConfig:
    """
    便捷的路由函数

    Args:
        task_type: 任务类型

    Returns:
        最优模型配置
    """
    router = get_router()
    return router.route(task_type)


# ============ 测试代码 ============

if __name__ == "__main__":
    print("=" * 60)
    print("Abee Model Router Test")
    print("=" * 60)

    router = get_router()

    test_cases = [
        (TaskType.REALTIME, "实时任务（快速响应）"),
        (TaskType.REASONING, "推理任务（深度思考）"),
        (TaskType.CODING, "编码任务（代码生成）"),
        (TaskType.GENERATION, "生成任务（高质量输出）"),
    ]

    for task_type, description in test_cases:
        print(f"\n[{description}]")
        model = router.route(task_type)
        print(f"  Selected: {model.name} ({model.tier.value})")
        print(f"  Provider: {model.provider}")
        print(f"  Latency: {model.latency_ms}ms")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

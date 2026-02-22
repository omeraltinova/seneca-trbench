"""Model wrappers for Turkish Benchmark System."""

from .base_model import BaseModel
from .api_models import (
    OpenAIModel,
    AnthropicModel,
    TogetherModel,
    GeminiModel,
    OpenRouterModel,
    OllamaModel,
    LMStudioModel,
)
from .local_models import HuggingFaceModel

__all__ = [
    'BaseModel',
    'OpenAIModel',
    'AnthropicModel',
    'TogetherModel',
    'HuggingFaceModel',
    'GeminiModel',
    'OpenRouterModel',
    'OllamaModel',
    'LMStudioModel',
]


# Provider name -> Model class mapping (used by benchmark.py and judge.py)
PROVIDER_MAP = {
    'openai': OpenAIModel,
    'anthropic': AnthropicModel,
    'together': TogetherModel,
    'huggingface': HuggingFaceModel,
    'gemini': GeminiModel,
    'openrouter': OpenRouterModel,
    'ollama': OllamaModel,
    'lmstudio': LMStudioModel,
}


def create_model(provider: str, model_name: str, config: dict):
    """
    Create model instance based on provider.
    
    Args:
        provider: Provider name (openai, anthropic, together, huggingface, gemini,
                  openrouter, ollama, lmstudio)
        model_name: Model identifier
        config: Configuration dictionary
        
    Returns:
        Model instance
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDER_MAP:
        supported = ', '.join(sorted(PROVIDER_MAP.keys()))
        raise ValueError(f"Desteklenmeyen provider: '{provider}'. Desteklenenler: {supported}")
    
    return PROVIDER_MAP[provider](model_name, config)

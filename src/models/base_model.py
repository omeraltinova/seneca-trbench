"""Base model interface for all model wrappers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class BaseModel(ABC):
    """Abstract base class for all model implementations."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        """
        Initialize base model.
        
        Args:
            model_name: Name/identifier of the model
            config: Configuration dictionary
        """
        self.model_name = model_name
        self.config = config
        self._is_ready = False
    
    @property
    def supports_tool_calling(self) -> bool:
        """Whether this model supports tool/function calling.
        
        Override in subclasses that support tool calling.
        """
        return False
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        pass
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate response with tool/function calling.
        
        Args:
            prompt: Input prompt
            tools: List of tool definitions (OpenAI format)
            tool_choice: Tool selection strategy ("required", "auto", "none")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Dict with 'tool_name' (str) and 'arguments' (dict)
            
        Raises:
            NotImplementedError: If provider does not support tool calling
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} provider tool calling desteklemiyor. "
            f"--mcq-type ai kullanın."
        )
    
    @abstractmethod
    def setup(self) -> None:
        """
        Setup the model (download, load, start server, etc.).
        This is called before first use.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup resources (stop server, free memory, etc.).
        This is called when done with the model.
        """
        pass
    
    def is_ready(self) -> bool:
        """Check if model is ready for inference."""
        return self._is_ready
    
    def __enter__(self):
        """Context manager entry."""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False


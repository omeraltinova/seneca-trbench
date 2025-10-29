"""Base model interface for all model wrappers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


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


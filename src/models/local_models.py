"""Local model implementation with HuggingFace Transformers (Mac uyumlu)."""

import torch
from pathlib import Path
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_model import BaseModel


class HuggingFaceModel(BaseModel):
    """HuggingFace model with direct Transformers (Mac/CPU/GPU uyumlu)."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.local_config = config.get('local', {})
        self.download_dir = self.local_config.get('download_dir', './models')
        self.max_model_len = self.local_config.get('max_model_len', 4096)
        
        self.pipeline = None
        self.device = None
        self.model_path = None
    
    def _get_device(self) -> str:
        """Detect best available device (CUDA > MPS > CPU)."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"  # Apple Silicon
        else:
            return "cpu"
    
    def _download_model(self) -> str:
        """Download model from HuggingFace if not already cached."""
        try:
            from huggingface_hub import snapshot_download
            
            print(f"📥 Model indiriliyor: {self.model_name}")
            model_path = snapshot_download(
                repo_id=self.model_name,
                cache_dir=self.download_dir,
                resume_download=True
            )
            print(f"✓ Model indirildi: {model_path}")
            return model_path
        except ImportError:
            raise ImportError("huggingface-hub package required. Install with: pip install huggingface-hub")
        except Exception as e:
            raise Exception(f"Model indirme hatası: {str(e)}")
    
    def setup(self) -> None:
        """Load model with Transformers pipeline."""
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            
            # Download model
            self.model_path = self._download_model()
            
            # Detect device
            self.device = self._get_device()
            device_name = {
                "cuda": "NVIDIA GPU",
                "mps": "Apple Silicon GPU",
                "cpu": "CPU"
            }.get(self.device, self.device)
            print(f"🖥️  Cihaz: {device_name}")
            
            # Load model with appropriate settings
            print(f"⚙️  Model yükleniyor...")
            
            # For Mac/CPU: use smaller precision and optimizations
            model_kwargs = {
                "cache_dir": self.download_dir,
                "low_cpu_mem_usage": True,
            }
            
            if self.device == "cpu":
                print("⚠️  CPU modunda çalışıyor - yavaş olabilir")
                # CPU optimizations
                model_kwargs["torch_dtype"] = torch.float32
            elif self.device == "mps":
                print("🍎 Apple Silicon GPU kullanılıyor")
                model_kwargs["torch_dtype"] = torch.float16
            else:
                # CUDA
                model_kwargs["torch_dtype"] = torch.float16
                model_kwargs["device_map"] = "auto"
            
            # Create pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.model_name,
                device=self.device if self.device != "cuda" else 0,
                model_kwargs=model_kwargs,
                max_length=self.max_model_len,
            )
            
            print(f"✓ Model hazır!")
            self._is_ready = True
            
        except Exception as e:
            self._is_ready = False
            raise Exception(f"Model kurulum hatası: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using Transformers pipeline."""
        if not self._is_ready:
            raise RuntimeError("Model hazır değil. Önce setup() çağrılmalı.")
        
        try:
            # Generate with pipeline
            output = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=kwargs.get('top_p', 0.9),
                top_k=kwargs.get('top_k', 50),
                num_return_sequences=1,
                pad_token_id=self.pipeline.tokenizer.eos_token_id,
                truncation=True,
            )
            
            # Extract generated text (remove prompt)
            generated_text = output[0]['generated_text']
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            raise Exception(f"Transformers inference hatası: {str(e)}")
    
    def cleanup(self) -> None:
        """Cleanup model from memory."""
        if self.pipeline:
            print("🧹 Model bellekten temizleniyor...")
            del self.pipeline
            self.pipeline = None
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            
            print("✓ Model temizlendi.")
        
        self._is_ready = False

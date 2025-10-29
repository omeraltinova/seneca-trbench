"""API-based model implementations."""

import time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_model import BaseModel


class OpenAIModel(BaseModel):
    """OpenAI API model wrapper."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        # Preserve original and normalize to known API identifiers
        self.original_model_name = model_name
        self.model_name = self._normalize_model_name(model_name)
        self.api_key = config.get('api_providers', {}).get('openai', {}).get('api_key')
        self.base_url = config.get('api_providers', {}).get('openai', {}).get('base_url')
        self.client = None
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found in config or environment")

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        """Map friendly/synonym names to official API model IDs."""
        aliases = {
            # GPT-5 friendly → official
            'gpt-5-main': 'gpt-5',
            'gpt-5-main-mini': 'gpt-5-mini',
            'gpt-5-thinking': 'gpt-5-pro',  # thinking ≈ pro (en güçlü)
            'gpt-5-thinking-mini': 'gpt-5-mini',
            'gpt-5-thinking-nano': 'gpt-5-nano',
            # Historical fallbacks
            'gpt-5-chat': 'gpt-5-chat-latest',
        }
        return aliases.get(name, name)
    
    def setup(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            # Preflight: validate model exists and is accessible
            try:
                # Some environments may not allow model retrieve; ignore if endpoint unavailable
                self.client.models.retrieve(self.model_name)
            except Exception as e:  # noqa: BLE001 - propagate meaningful error below if truly missing
                msg = str(e)
                if any(tok in msg.lower() for tok in ["not found", "does not exist", "unknown model", "404", "invalid model"]):
                    raise Exception(
                        f"Model '{self.model_name}' mevcut değil veya erişilemiyor. Lütfen doğru model adını kullanın.")
            self._is_ready = True
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using OpenAI API."""
        if not self._is_ready:
            self.setup()
        
        try:
            # Ensure 'timeout' is passed only once
            timeout_s = (
                self.config.get('test_settings', {}).get('timeout_seconds', 60)
            )
            timeout_s = kwargs.pop('timeout', timeout_s)
            # Some GPT-5 models require 'max_completion_tokens' instead of 'max_tokens'
            use_max_completion_tokens = self.model_name.startswith('gpt-5')
            payload = {
                'model': self.model_name,
                'messages': [{"role": "user", "content": prompt}],
                # GPT-5: only default(1) temperature supported — güvenli değer
                'temperature': 1 if use_max_completion_tokens else temperature,
                'timeout': timeout_s,
            }
            if use_max_completion_tokens:
                payload['max_completion_tokens'] = max_tokens
            else:
                payload['max_tokens'] = max_tokens

            response = self.client.chat.completions.create(
                **payload,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # tenacity RetryError sarmalamasını açığa çıkar
            error_obj = getattr(e, 'last_attempt', None).exception if hasattr(e, 'last_attempt') else e
            error_msg = str(error_obj)
            # If model requires Responses API, fallback
            if any(s in error_msg.lower() for s in [
                'use the responses api',
                'not supported with the v1/chat/completions endpoint',
                'try responses.create',
                "unsupported parameter: 'max_tokens'",
                "unsupported value: 'temperature'",
            ]):
                try:
                    resp = self.client.responses.create(
                        model=self.model_name,
                        input=prompt,
                        temperature=1 if self.model_name.startswith('gpt-5') else temperature,
                        max_output_tokens=max_tokens,
                        timeout=timeout_s,
                    )
                    # Best-effort text extraction across possible SDK shapes
                    if hasattr(resp, 'output_text') and resp.output_text:
                        return resp.output_text.strip()
                    if hasattr(resp, 'output') and resp.output:
                        try:
                            first = resp.output[0]
                            if hasattr(first, 'content') and first.content:
                                part = first.content[0]
                                if hasattr(part, 'text') and part.text:
                                    return part.text.strip()
                        except Exception:
                            pass
                    if hasattr(resp, 'choices') and resp.choices:
                        choice = resp.choices[0]
                        if getattr(choice, 'message', None) and getattr(choice.message, 'content', None):
                            return choice.message.content.strip()
                    # Last fallback: try to_dict/model_dump
                    for attr in ('model_dump', 'to_dict'):
                        fn = getattr(resp, attr, None)
                        if fn:
                            data = fn()
                            # Try common paths
                            try:
                                return data['output'][0]['content'][0]['text'].strip()
                            except Exception:
                                pass
                    raise Exception('OpenAI Responses API: içerik çözümlenemedi')
                except Exception as e2:
                    raise Exception(f"OpenAI Responses API hatası ({self.model_name}): {str(e2)}")
            # Check for common errors
            if "model" in error_msg.lower() and "does not exist" in error_msg.lower():
                raise Exception(f"Model '{self.model_name}' mevcut değil. Lütfen geçerli bir model adı kullanın. Hata: {error_msg}")
            elif "rate_limit" in error_msg.lower():
                raise Exception(f"Rate limit aşıldı. Lütfen bekleyin. Hata: {error_msg}")
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                raise Exception(f"API key hatası. Lütfen OPENAI_API_KEY'i kontrol edin. Hata: {error_msg}")
            else:
                raise Exception(f"OpenAI API hatası ({self.model_name}): {error_msg}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.client = None
        self._is_ready = False


class AnthropicModel(BaseModel):
    """Anthropic API model wrapper."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.api_key = config.get('api_providers', {}).get('anthropic', {}).get('api_key')
        self.client = None
        
        if not self.api_key:
            raise ValueError("Anthropic API key not found in config or environment")
    
    def setup(self) -> None:
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self._is_ready = True
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using Anthropic API."""
        if not self._is_ready:
            self.setup()
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.content[0].text.strip()
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.client = None
        self._is_ready = False


class TogetherModel(BaseModel):
    """Together AI API model wrapper."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.api_key = config.get('api_providers', {}).get('together', {}).get('api_key')
        self.base_url = config.get('api_providers', {}).get('together', {}).get('base_url')
        self.client = None
        
        if not self.api_key:
            raise ValueError("Together API key not found in config or environment")
    
    def setup(self) -> None:
        """Initialize Together client."""
        try:
            from openai import OpenAI  # Together uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            self._is_ready = True
        except ImportError:
            raise ImportError("openai package is required for Together API. Install with: pip install openai")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using Together API."""
        if not self._is_ready:
            self.setup()
        
        try:
            # Ensure 'timeout' is passed only once
            timeout_s = (
                self.config.get('test_settings', {}).get('timeout_seconds', 60)
            )
            timeout_s = kwargs.pop('timeout', timeout_s)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_s,
                **kwargs
            )
            # Primary extraction path
            if hasattr(response, 'choices') and response.choices:
                first = response.choices[0]
                # chat.message.content can be str or list of segments
                if getattr(first, 'message', None) and getattr(first.message, 'content', None):
                    content = first.message.content
                    if isinstance(content, str):
                        return content.strip()
                    if isinstance(content, list):
                        texts = []
                        for seg in content:
                            # segment may be {type: 'text', text: '...'}
                            if isinstance(seg, dict) and 'text' in seg:
                                texts.append(seg['text'])
                        if texts:
                            return "".join(texts).strip()
                # non-chat completion style
                if getattr(first, 'text', None):
                    return first.text.strip()
            # Fallbacks for Together variants
            if hasattr(response, 'output_text') and response.output_text:
                return response.output_text.strip()
            for attr in ('model_dump', 'to_dict'):
                fn = getattr(response, attr, None)
                if fn:
                    data = fn()
                    try:
                        if data.get('choices'):
                            content = data['choices'][0].get('message', {}).get('content')
                            if content:
                                return content.strip()
                        if data.get('error'):
                            err = data['error']
                            code = err.get('code', 'error')
                            message = err.get('message', '')
                            raise Exception(f"{code}: {message}")
                    except Exception:
                        pass
            # Try Responses API if available
            try:
                resp = self.client.responses.create(
                    model=self.model_name,
                    input=prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    timeout=timeout_s,
                )
                if hasattr(resp, 'output_text') and resp.output_text:
                    return resp.output_text.strip()
            except Exception:
                pass
            # Last fallback: legacy completions endpoint
            try:
                legacy = self.client.completions.create(
                    model=self.model_name,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout_s,
                )
                if hasattr(legacy, 'choices') and legacy.choices:
                    txt = getattr(legacy.choices[0], 'text', None)
                    if txt:
                        return txt.strip()
            except Exception:
                pass
            raise Exception('Empty response (choices yok). Model veya parametreler Together ile uyumsuz olabilir.')
        except Exception as e:
            raise Exception(f"Together API error: {str(e)}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.client = None
        self._is_ready = False


class GeminiModel(BaseModel):
    """Google Gemini API model wrapper (REST generateContent)."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        gem_cfg = config.get('api_providers', {}).get('gemini', {})
        self.api_key = gem_cfg.get('api_key')
        self.base_url = gem_cfg.get('base_url', 'https://generativelanguage.googleapis.com')
        self.api_version = gem_cfg.get('api_version', 'v1beta')
        if not self.api_key:
            raise ValueError("Gemini API key not found in config or environment")
        # Guard against misconfigured endpoints (anahtar formatını engellemeyelim)
        # Normalize base_url if mistakenly set to Together/OpenAI
        if isinstance(self.base_url, str) and ('together' in self.base_url or 'openai' in self.base_url):
            self.base_url = 'https://generativelanguage.googleapis.com'
        self._is_ready = False
    
    def setup(self) -> None:
        """No client object needed; REST via requests."""
        self._is_ready = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using Gemini generateContent endpoint."""
        if not self._is_ready:
            self.setup()
        
        import requests
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
        timeout_s = kwargs.pop('timeout', timeout_s)
        # Build URL with API key as query parameter (per Gemini docs)
        # Ensure correct host even if config was wrong at runtime
        base_url = self.base_url if 'googleapis.com' in self.base_url else 'https://generativelanguage.googleapis.com'
        url = f"{base_url}/{self.api_version}/models/{self.model_name}:generateContent?key={self.api_key}"
        
        # Map params to generationConfig
        generation_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        # Remove None values
        generation_config = {k: v for k, v in generation_config.items() if v is not None}
        
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                    ],
                }
            ],
            "generationConfig": generation_config,
        }
        
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            # Typical path: candidates[0].content.parts[*].text
            candidates = data.get("candidates") or []
            if candidates:
                content = candidates[0].get("content") or {}
                parts = content.get("parts") or []
                texts = []
                for p in parts:
                    if isinstance(p, dict) and p.get("text"):
                        texts.append(p["text"])
                if texts:
                    return "".join(texts).strip()
            # If direct text field exists
            if data.get("text"):
                return str(data["text"]).strip()
            # Fallback raw string
            return str(data)
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def cleanup(self) -> None:
        self._is_ready = False

"""API-based model implementations."""

import json
import time
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_model import BaseModel


def _openai_tool_call(client, model_name: str, prompt: str, tools: List[Dict[str, Any]],
                      tool_choice: str, temperature: float, max_tokens: int,
                      timeout_s: int, **kwargs) -> Dict[str, Any]:
    """
    Shared tool-calling logic for all OpenAI-compatible providers.
    
    Args:
        client: OpenAI-compatible client instance
        model_name: Model identifier
        prompt: Input prompt
        tools: Tool definitions (OpenAI format)
        tool_choice: Tool selection strategy
        temperature: Sampling temperature
        max_tokens: Max tokens
        timeout_s: Timeout in seconds
        
    Returns:
        Dict with 'tool_name' and 'arguments'
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout_s,
        **kwargs,
    )
    
    message = response.choices[0].message
    
    if not message.tool_calls:
        raise Exception("Model tool call yapmadı. Serbest metin cevabı döndü.")
    
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    
    return {
        'tool_name': tool_call.function.name,
        'arguments': arguments,
    }


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
    
    @property
    def supports_tool_calling(self) -> bool:
        return True

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
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via OpenAI API."""
        if not self._is_ready:
            self.setup()
        
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        try:
            return _openai_tool_call(
                client=self.client,
                model_name=self.model_name,
                prompt=prompt,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                **kwargs,
            )
        except Exception as e:
            raise Exception(f"OpenAI tool call hatası ({self.model_name}): {str(e)}")


class AnthropicModel(BaseModel):
    """Anthropic API model wrapper."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.api_key = config.get('api_providers', {}).get('anthropic', {}).get('api_key')
        self.client = None
        
        if not self.api_key:
            raise ValueError("Anthropic API key not found in config or environment")
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
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
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via Anthropic API."""
        if not self._is_ready:
            self.setup()
        
        # Anthropic tool format: convert from OpenAI format
        anthropic_tools = []
        for tool in tools:
            func = tool.get('function', tool)
            anthropic_tools.append({
                'name': func['name'],
                'description': func.get('description', ''),
                'input_schema': func['parameters'],
            })
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                tools=anthropic_tools,
                tool_choice={"type": "any"} if tool_choice == "required" else {"type": tool_choice},
            )
            
            # Anthropic: tool_use content bloğundan çıkar
            for block in response.content:
                if block.type == 'tool_use':
                    return {
                        'tool_name': block.name,
                        'arguments': block.input,
                    }
            
            raise Exception("Model tool call yapmadı. Serbest metin cevabı döndü.")
            
        except Exception as e:
            raise Exception(f"Anthropic tool call hatası ({self.model_name}): {str(e)}")


class TogetherModel(BaseModel):
    """Together AI API model wrapper."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.api_key = config.get('api_providers', {}).get('together', {}).get('api_key')
        self.base_url = config.get('api_providers', {}).get('together', {}).get('base_url')
        self.client = None
        
        if not self.api_key:
            raise ValueError("Together API key not found in config or environment")
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
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
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via Together API."""
        if not self._is_ready:
            self.setup()
        
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        try:
            return _openai_tool_call(
                client=self.client,
                model_name=self.model_name,
                prompt=prompt,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                **kwargs,
            )
        except Exception as e:
            raise Exception(f"Together tool call hatası ({self.model_name}): {str(e)}")


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
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
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
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via Gemini REST API."""
        if not self._is_ready:
            self.setup()
        
        import requests as req_lib
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        base_url = self.base_url if 'googleapis.com' in self.base_url else 'https://generativelanguage.googleapis.com'
        url = f"{base_url}/{self.api_version}/models/{self.model_name}:generateContent?key={self.api_key}"
        
        # Gemini tool format: convert from OpenAI format
        function_declarations = []
        for tool in tools:
            func = tool.get('function', tool)
            # Gemini requires uppercase type names
            params = func.get('parameters', {})
            gemini_params = {
                'type': params.get('type', 'OBJECT').upper(),
                'properties': {},
                'required': params.get('required', []),
            }
            for prop_name, prop_def in params.get('properties', {}).items():
                gemini_prop = {
                    'type': prop_def.get('type', 'STRING').upper(),
                    'description': prop_def.get('description', ''),
                }
                if 'enum' in prop_def:
                    gemini_prop['enum'] = prop_def['enum']
                gemini_params['properties'][prop_name] = gemini_prop
            
            function_declarations.append({
                'name': func['name'],
                'description': func.get('description', ''),
                'parameters': gemini_params,
            })
        
        payload: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "tools": [{"functionDeclarations": function_declarations}],
            "toolConfig": {"functionCallingConfig": {"mode": "ANY"}},
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        
        try:
            resp = req_lib.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if "functionCall" in part:
                        fc = part["functionCall"]
                        return {
                            'tool_name': fc['name'],
                            'arguments': fc.get('args', {}),
                        }
            
            raise Exception("Model tool call yapmadı. Serbest metin cevabı döndü.")
            
        except Exception as e:
            raise Exception(f"Gemini tool call hatası ({self.model_name}): {str(e)}")


class OpenRouterModel(BaseModel):
    """OpenRouter API model wrapper (OpenAI-compatible)."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        or_cfg = config.get('api_providers', {}).get('openrouter', {})
        self.api_key = or_cfg.get('api_key')
        self.base_url = or_cfg.get('base_url', 'https://openrouter.ai/api/v1')
        self.site_url = or_cfg.get('site_url', '')
        self.site_name = or_cfg.get('site_name', 'Seneca-TRBench')
        self.client = None
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not found in config or environment. Set OPENROUTER_API_KEY.")
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
    def setup(self) -> None:
        """Initialize OpenRouter client via OpenAI SDK."""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                }
            )
            self._is_ready = True
        except ImportError:
            raise ImportError("openai package is required for OpenRouter. Install with: pip install openai")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using OpenRouter API."""
        if not self._is_ready:
            self.setup()
        
        try:
            timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
            timeout_s = kwargs.pop('timeout', timeout_s)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_s,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenRouter API error ({self.model_name}): {str(e)}")
    
    def cleanup(self) -> None:
        self.client = None
        self._is_ready = False
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via OpenRouter API."""
        if not self._is_ready:
            self.setup()
        
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 60)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        try:
            return _openai_tool_call(
                client=self.client,
                model_name=self.model_name,
                prompt=prompt,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                **kwargs,
            )
        except Exception as e:
            raise Exception(f"OpenRouter tool call hatası ({self.model_name}): {str(e)}")


class OllamaModel(BaseModel):
    """Ollama API model wrapper (OpenAI-compatible)."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        ol_cfg = config.get('api_providers', {}).get('ollama', {})
        self.api_key = ol_cfg.get('api_key', 'ollama')  # Ollama doesn't need a real key
        self.base_url = ol_cfg.get('base_url', 'http://localhost:11434/v1')
        self.client = None
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
    def setup(self) -> None:
        """Initialize Ollama client via OpenAI SDK."""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self._is_ready = True
        except ImportError:
            raise ImportError("openai package is required for Ollama. Install with: pip install openai")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using Ollama API."""
        if not self._is_ready:
            self.setup()
        
        try:
            timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 120)
            timeout_s = kwargs.pop('timeout', timeout_s)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_s,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                raise Exception(
                    f"Ollama'ya bağlanılamadı ({self.base_url}). "
                    f"Ollama'nın çalıştığından emin olun: 'ollama serve'"
                )
            raise Exception(f"Ollama API error ({self.model_name}): {error_msg}")
    
    def cleanup(self) -> None:
        self.client = None
        self._is_ready = False
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via Ollama API."""
        if not self._is_ready:
            self.setup()
        
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 120)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        try:
            return _openai_tool_call(
                client=self.client,
                model_name=self.model_name,
                prompt=prompt,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                **kwargs,
            )
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                raise Exception(
                    f"Ollama'ya bağlanılamadı ({self.base_url}). "
                    f"Ollama'nın çalıştığından emin olun: 'ollama serve'"
                )
            raise Exception(f"Ollama tool call hatası ({self.model_name}): {error_msg}")


class LMStudioModel(BaseModel):
    """LM Studio API model wrapper (OpenAI-compatible)."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        lm_cfg = config.get('api_providers', {}).get('lmstudio', {})
        self.api_key = lm_cfg.get('api_key', 'lm-studio')  # LM Studio doesn't need a real key
        self.base_url = lm_cfg.get('base_url', 'http://localhost:1234/v1')
        self.client = None
    
    @property
    def supports_tool_calling(self) -> bool:
        return True
    
    def setup(self) -> None:
        """Initialize LM Studio client via OpenAI SDK."""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            self._is_ready = True
        except ImportError:
            raise ImportError("openai package is required for LM Studio. Install with: pip install openai")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs) -> str:
        """Generate text using LM Studio API."""
        if not self._is_ready:
            self.setup()
        
        try:
            timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 120)
            timeout_s = kwargs.pop('timeout', timeout_s)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout_s,
                **kwargs
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                raise Exception(
                    f"LM Studio'ya bağlanılamadı ({self.base_url}). "
                    f"LM Studio'nun çalıştığından ve Local Server'ın aktif olduğundan emin olun."
                )
            raise Exception(f"LM Studio API error ({self.model_name}): {error_msg}")
    
    def cleanup(self) -> None:
        self.client = None
        self._is_ready = False
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "required",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool calling via LM Studio API."""
        if not self._is_ready:
            self.setup()
        
        timeout_s = self.config.get('test_settings', {}).get('timeout_seconds', 120)
        timeout_s = kwargs.pop('timeout', timeout_s)
        
        try:
            return _openai_tool_call(
                client=self.client,
                model_name=self.model_name,
                prompt=prompt,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                **kwargs,
            )
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                raise Exception(
                    f"LM Studio'ya bağlanılamadı ({self.base_url}). "
                    f"LM Studio'nun çalıştığından ve Local Server'ın aktif olduğundan emin olun."
                )
            raise Exception(f"LM Studio tool call hatası ({self.model_name}): {error_msg}")

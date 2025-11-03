"""
LLM Facade - Unified interface for multiple LLM providers
Supports Anthropic, OpenAI, Google, Meta, DeepSeek, AWS Bedrock, HuggingFace

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import os
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMConfig:
    """LLM configuration manager with auto-refresh"""

    def __init__(self, config_path: str = 'config/llm/llm.json'):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.last_loaded: Optional[datetime] = None
        self.refresh_interval: int = 600  # 10 minutes default
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()

        # Load initial configuration
        self.load_config()

        # Start auto-refresh thread
        self.start_auto_refresh()

    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            # Support multiple config locations
            config_paths = [
                self.config_path,
                'config/llm/llm.json',
                'llm_config.json',
                '/home/claude/llm_config.json'
            ]

            config_file = None
            for path in config_paths:
                if os.path.exists(path):
                    config_file = path
                    break

            if not config_file:
                logger.warning(f"Config file not found, using defaults")
                self._load_default_config()
                return False

            with open(config_file, 'r') as f:
                new_config = json.load(f)

            with self._lock:
                self.config = new_config
                self.last_loaded = datetime.now()
                self.refresh_interval = new_config.get('refresh_interval_seconds', 600)

            logger.info(f"Loaded LLM config from {config_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._load_default_config()
            return False

    def _load_default_config(self):
        """Load default configuration if file not found"""
        with self._lock:
            self.config = {
                'default_provider': 'mock',
                'default_model': 'mock-llm',
                'fallback_provider': 'mock',
                'providers': {
                    'mock': {
                        'enabled': True,
                        'models': {
                            'mock-llm': {
                                'enabled': True,
                                'model_id': 'mock-llm-v1',
                                'description': 'Mock LLM for testing'
                            }
                        }
                    }
                }
            }
            self.last_loaded = datetime.now()

    def start_auto_refresh(self):
        """Start background thread for auto-refresh"""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self._refresh_thread.start()
        logger.info(f"Started auto-refresh thread (interval: {self.refresh_interval}s)")

    def stop_auto_refresh(self):
        """Stop auto-refresh thread"""
        self._stop_refresh.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=2)
        logger.info("Stopped auto-refresh thread")

    def _auto_refresh_loop(self):
        """Background loop for auto-refresh"""
        while not self._stop_refresh.is_set():
            try:
                time.sleep(self.refresh_interval)
                if not self._stop_refresh.is_set():
                    logger.debug("Auto-refreshing LLM config")
                    self.load_config()
            except Exception as e:
                logger.error(f"Error in auto-refresh: {e}")

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration (thread-safe)"""
        with self._lock:
            return self.config.copy()

    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific provider"""
        with self._lock:
            return self.config.get('providers', {}).get(provider)

    def get_model_config(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific model"""
        provider_config = self.get_provider_config(provider)
        if provider_config:
            return provider_config.get('models', {}).get(model)
        return None

    def get_enabled_models(self) -> List[Dict[str, Any]]:
        """Get list of all enabled models"""
        enabled_models = []
        config = self.get_config()

        for provider_name, provider_config in config.get('providers', {}).items():
            if not provider_config.get('enabled', False):
                continue

            for model_name, model_config in provider_config.get('models', {}).items():
                if model_config.get('enabled', False):
                    enabled_models.append({
                        'provider': provider_name,
                        'model': model_name,
                        'model_id': model_config.get('model_id'),
                        'description': model_config.get('description'),
                        'best_for': model_config.get('best_for', [])
                    })

        return enabled_models

    def get_default_provider_model(self) -> tuple[str, str]:
        """Get default provider and model"""
        config = self.get_config()
        return (
            config.get('default_provider', 'mock'),
            config.get('default_model', 'mock-llm')
        )


class LLMFacade:
    """Unified facade for multiple LLM providers"""

    # Shared configuration instance
    _config_instance: Optional[LLMConfig] = None
    _config_lock = threading.Lock()

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None,
                 config_path: Optional[str] = None):
        """
        Initialize LLM Facade

        Args:
            provider: LLM provider (anthropic, openai, google, etc.) - uses default if None
            model: Model name - uses default for provider if None
            config_path: Path to config file - uses default if None
        """
        # Load environment variables (ensure they're available in workflow threads)
        from dotenv import load_dotenv
        load_dotenv(override=True)

        # Initialize shared config if needed
        with self._config_lock:
            if LLMFacade._config_instance is None:
                config_file = config_path or 'config/llm/llm.json'
                LLMFacade._config_instance = LLMConfig(config_file)

        self.config_manager = LLMFacade._config_instance

        # Determine provider and model
        if provider is None or model is None:
            default_provider, default_model = self.config_manager.get_default_provider_model()
            self.provider = provider or default_provider
            self.model = model or default_model
        else:
            self.provider = provider
            self.model = model

        # Get model configuration
        self.model_config = self.config_manager.get_model_config(self.provider, self.model)
        self.provider_config = self.config_manager.get_provider_config(self.provider)

        logger.info(f"Initialized LLMFacade: {self.provider}/{self.model}")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using configured LLM

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text
        """
        try:
            if self.provider == 'anthropic':
                return self._anthropic_generate(prompt, **kwargs)
            elif self.provider == 'openai':
                return self._openai_generate(prompt, **kwargs)
            elif self.provider == 'google':
                return self._google_generate(prompt, **kwargs)
            elif self.provider == 'meta':
                return self._meta_generate(prompt, **kwargs)
            elif self.provider == 'deepseek':
                return self._deepseek_generate(prompt, **kwargs)
            elif self.provider == 'aws_bedrock':
                return self._bedrock_generate(prompt, **kwargs)
            elif self.provider == 'huggingface':
                return self._huggingface_generate(prompt, **kwargs)
            elif self.provider == 'mock':
                return self._mock_generate(prompt, **kwargs)
            else:
                logger.warning(f"Unknown provider {self.provider}, falling back to mock")
                return self._mock_generate(prompt, **kwargs)

        except Exception as e:
            logger.error(f"Error generating with {self.provider}: {e}")
            # Fallback to mock
            return self._mock_generate(prompt, **kwargs)

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate structured output (JSON) based on schema

        Args:
            prompt: Input prompt
            schema: JSON schema for output
            **kwargs: Additional parameters

        Returns:
            Structured output as dictionary
        """
        # Add schema to prompt for models without native structured output
        structured_prompt = f"""{prompt}

Please provide your response as valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Return ONLY the JSON, no other text."""

        response = self.generate(structured_prompt, **kwargs)

        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except:
            logger.warning("Could not parse structured response, returning raw text")
            return {'response': response}

    def _anthropic_generate(self, prompt: str, **kwargs) -> str:
        """Generate using Anthropic Claude"""
        try:
            import anthropic

            api_key = os.getenv(self.provider_config.get('api_key_env', 'ANTHROPIC_API_KEY'))
            if not api_key:
                raise ValueError("Anthropic API key not found")

            client = anthropic.Anthropic(api_key=api_key)

            model_id = self.model_config.get('model_id', 'claude-sonnet-4-5-20250929')
            max_tokens = kwargs.get('max_tokens', 4096)
            temperature = kwargs.get('temperature', 1.0)

            response = client.messages.create(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def _openai_generate(self, prompt: str, **kwargs) -> str:
        """Generate using OpenAI"""
        try:
            import openai

            api_key = os.getenv(self.provider_config.get('api_key_env', 'OPENAI_API_KEY'))
            if not api_key:
                raise ValueError("OpenAI API key not found")

            client = openai.OpenAI(api_key=api_key)

            model_id = self.model_config.get('model_id', 'gpt-4o')
            max_tokens = kwargs.get('max_tokens', 4096)
            temperature = kwargs.get('temperature', 1.0)

            response = client.chat.completions.create(
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _google_generate(self, prompt: str, **kwargs) -> str:
        """Generate using Google Gemini"""
        try:
            import google.generativeai as genai

            api_key = os.getenv(self.provider_config.get('api_key_env', 'GOOGLE_API_KEY'))
            if not api_key:
                raise ValueError("Google API key not found")

            genai.configure(api_key=api_key)

            model_id = self.model_config.get('model_id', 'gemini-1.5-pro')
            temperature = kwargs.get('temperature', 1.0)

            model = genai.GenerativeModel(model_id)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )

            return response.text

        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise

    def _meta_generate(self, prompt: str, **kwargs) -> str:
        """Generate using Meta Llama (via third-party API)"""
        try:
            import requests

            api_key = os.getenv(self.provider_config.get('api_key_env', 'META_API_KEY'))
            if not api_key:
                raise ValueError("Meta API key not found")

            base_url = self.provider_config.get('base_url')
            model_id = self.model_config.get('model_id')

            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get('temperature', 1.0),
                    "max_tokens": kwargs.get('max_tokens', 4096)
                },
                timeout=60
            )

            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"Meta API error: {e}")
            raise

    def _deepseek_generate(self, prompt: str, **kwargs) -> str:
        """Generate using DeepSeek"""
        try:
            import requests

            api_key = os.getenv(self.provider_config.get('api_key_env', 'DEEPSEEK_API_KEY'))
            if not api_key:
                raise ValueError("DeepSeek API key not found")

            base_url = self.provider_config.get('base_url')
            model_id = self.model_config.get('model_id')

            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get('temperature', 1.0),
                    "max_tokens": kwargs.get('max_tokens', 4096)
                },
                timeout=60
            )

            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise

    def _bedrock_generate(self, prompt: str, **kwargs) -> str:
        """Generate using AWS Bedrock"""
        try:
            import boto3
            import json

            # AWS credentials from environment
            region = self.provider_config.get('region', 'us-east-1')

            client = boto3.client('bedrock-runtime', region_name=region)

            model_id = self.model_config.get('model_id')

            # Format depends on model
            if 'anthropic' in model_id:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": kwargs.get('max_tokens', 4096),
                    "temperature": kwargs.get('temperature', 1.0),
                    "messages": [{"role": "user", "content": prompt}]
                }
            elif 'titan' in model_id:
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": kwargs.get('max_tokens', 4096),
                        "temperature": kwargs.get('temperature', 1.0)
                    }
                }
            else:
                raise ValueError(f"Unsupported Bedrock model: {model_id}")

            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response['body'].read())

            # Extract text based on model
            if 'anthropic' in model_id:
                return response_body['content'][0]['text']
            elif 'titan' in model_id:
                return response_body['results'][0]['outputText']
            else:
                return str(response_body)

        except Exception as e:
            logger.error(f"Bedrock API error: {e}")
            raise

    def _huggingface_generate(self, prompt: str, **kwargs) -> str:
        """Generate using HuggingFace Inference API"""
        try:
            import requests

            api_key = os.getenv(self.provider_config.get('api_key_env', 'HUGGINGFACE_API_KEY'))
            if not api_key:
                raise ValueError("HuggingFace API key not found")

            base_url = self.provider_config.get('base_url')
            model_id = self.model_config.get('model_id')

            response = requests.post(
                f"{base_url}/{model_id}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": kwargs.get('max_tokens', 1024),
                        "temperature": kwargs.get('temperature', 1.0)
                    }
                },
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            if isinstance(result, list):
                return result[0].get('generated_text', '')
            return result.get('generated_text', str(result))

        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            raise

    def _mock_generate(self, prompt: str, **kwargs) -> str:
        """Mock LLM for testing"""
        prompt_lower = prompt.lower()

        if 'create a plan' in prompt_lower or 'plan for' in prompt_lower:
            return """Based on your request, here's a suggested workflow plan:

1. Initialize the workflow
2. Fetch required data
3. Process the data
4. Validate results
5. Generate output
6. Send notifications

This plan can be executed as a sequential workflow with appropriate tools and agents."""

        elif 'json' in prompt_lower and 'schema' in prompt_lower:
            return """{
  "dag_id": "generated_plan_001",
  "name": "Sample Workflow Plan",
  "description": "Auto-generated workflow plan",
  "nodes": [
    {
      "node_id": "step_1",
      "node_type": "agent",
      "agent_id": "echo_agent",
      "config": {"input": {}},
      "dependencies": []
    }
  ],
  "start_nodes": ["step_1"]
}"""

        elif 'tools available' in prompt_lower:
            return "Available tools include: echo, get_stock_price, get_stock_info, and other MCP tools."

        elif 'agents available' in prompt_lower:
            return "Available agents include: echo_agent and other configured agents."

        else:
            return f"I understand you're asking about: {prompt[:100]}... I can help you create workflow plans, execute tasks, and coordinate agents. What would you like to do?"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        return {
            'provider': self.provider,
            'model': self.model,
            'model_id': self.model_config.get('model_id') if self.model_config else None,
            'description': self.model_config.get('description') if self.model_config else None,
            'best_for': self.model_config.get('best_for', []) if self.model_config else [],
            'supports_vision': self.model_config.get('supports_vision', False) if self.model_config else False,
            'supports_function_calling': self.model_config.get('supports_function_calling', False) if self.model_config else False,
            'context_window': self.model_config.get('context_window', 0) if self.model_config else 0
        }

    @staticmethod
    def list_available_models() -> List[Dict[str, Any]]:
        """List all available models"""
        if LLMFacade._config_instance:
            return LLMFacade._config_instance.get_enabled_models()
        return []

    @staticmethod
    def get_recommended_model(task_type: str) -> tuple[str, str]:
        """
        Get recommended model for specific task type

        Args:
            task_type: Type of task (coding, reasoning, planning, etc.)

        Returns:
            Tuple of (provider, model)
        """
        if not LLMFacade._config_instance:
            return ('mock', 'mock-llm')

        task_type_lower = task_type.lower()
        models = LLMFacade._config_instance.get_enabled_models()

        # Score models based on task type
        best_match = None
        best_score = 0

        for model_info in models:
            score = 0
            best_for = [bf.lower() for bf in model_info.get('best_for', [])]

            # Exact match
            if task_type_lower in best_for:
                score += 10

            # Partial match
            for bf in best_for:
                if task_type_lower in bf or bf in task_type_lower:
                    score += 5

            if score > best_score:
                best_score = score
                best_match = model_info

        if best_match:
            return (best_match['provider'], best_match['model'])

        # Fallback to default
        return LLMFacade._config_instance.get_default_provider_model()
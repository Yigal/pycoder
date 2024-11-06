from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import os
from pathlib import Path
import yaml
import json
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    code: str
    metadata: Dict[str, Any]

@dataclass
class AgentConfig:
    """Base configuration for all agents"""
    provider_name: str
    model: str
    temperature: float
    max_tokens: int
    context_length: int
    best_for: List[str]
    system_prompt: str
    
    @classmethod
    @abstractmethod
    def from_config(cls, config_path: str, model_name: Optional[str] = None) -> 'AgentConfig':
        """Create config from YAML file"""
        pass

class AgentError(Exception):
    """Base error for agent operations"""
    pass

class BaseAgent(ABC):
    """Base class for all code generation agents"""
    
    def __init__(self, config_path: str):
        """Initialize base agent with configuration path"""
        self.config_path = config_path
        self.config = None
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise AgentError(f"Failed to load settings: {str(e)}")

    def get_prompt_template(self, template_name: str) -> str:
        """Get prompt template from settings"""
        templates = self.settings.get('prompts', {})
        if template_name not in templates:
            raise AgentError(f"Unknown prompt template: {template_name}")
        return templates[template_name]

    def get_error_message(self, key: str, **kwargs) -> str:
        """Get formatted error message"""
        messages = self.settings.get('error_messages', {})
        message = messages.get(key, "Unknown error")
        return message.format(**kwargs)

    def validate_response_schema(self, 
                               response: Dict[str, Any],
                               schema_name: str) -> bool:
        """Validate response against schema"""
        schema = self.settings.get('response_schemas', {}).get(schema_name, {})
        required_fields = schema.get('required_fields', [])
        return all(field in response for field in required_fields)

    @abstractmethod
    async def generate_code(self, 
                          prompt_template: str,
                          requirements: str,
                          considerations: Optional[List[str]] = None) -> AgentResponse:
        """Generate code using the agent"""
        pass

    @abstractmethod
    async def validate_code(self, code: str) -> bool:
        """Validate generated code"""
        pass

    @abstractmethod
    async def improve_code(self, 
                         code: str,
                         aspects: List[str]) -> AgentResponse:
        """Improve existing code"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and configuration"""
        pass

    # Utility methods
    def format_prompt(self, 
                     template: str,
                     **kwargs) -> str:
        """Format prompt template with parameters"""
        return template.format(**kwargs)

    @staticmethod
    def format_list_items(items: List[str]) -> str:
        """Format list items for prompts"""
        return "\n".join(f"- {item}" for item in items)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry and backoff"""
        return await func(*args, **kwargs)

    async def parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response safely"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise AgentError(self.get_error_message('parse_error', details=str(e)))
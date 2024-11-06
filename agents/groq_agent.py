from typing import Dict, Any, Optional, List, AsyncIterator
import os
from groq import AsyncGroq
from groq.types import ChatCompletion, AsyncChatCompletionChunk

from .base_agent import BaseAgent, BaseAgentConfig, AgentError, AgentResponse

class GroqConfig(BaseAgentConfig):
    """Groq-specific configuration"""
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.validate_groq_config()
    
    def validate_groq_config(self):
        """Validate Groq-specific configuration"""
        required_fields = ['response_format', 'default_model', 'api_settings']
        for field in required_fields:
            if field not in self.provider_settings:
                raise AgentError(f"Missing required Groq config: {field}")
        
        # Validate Groq-specific settings
        api_settings = self.provider_settings['api_settings']
        required_api_settings = ['top_p', 'top_k']
        for setting in required_api_settings:
            if setting not in api_settings:
                raise AgentError(f"Missing required Groq API setting: {setting}")

class GroqAgent(BaseAgent):
    """
    Groq-based code generation agent
    
    This agent uses Groq's API for fast code generation with 
    models like Mixtral-8x7b and LLaMA2-70b.
    """
    
    def setup_client(self):
        """Set up Groq client"""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise AgentError(
                self.config.settings['error_messages']['api_key_missing']
                .format(provider='Groq')
            )
        self.client = AsyncGroq(api_key=api_key)
    
    def _load_config(self, config_path: str) -> GroqConfig:
        """Load Groq configuration"""
        return GroqConfig(config_path)

    async def generate_code(self,
                          prompt_template: str,
                          requirements: str,
                          considerations: Optional[List[str]] = None,
                          stream: bool = False) -> AgentResponse:
        """
        Generate code using Groq
        
        Args:
            prompt_template: Template name from configuration
            requirements: Code generation requirements
            considerations: Optional list of considerations
            stream: Whether to stream the response
        """
        try:
            # Get and format prompt
            template = self.get_prompt_template('code_generation')
            prompt = self.format_prompt(
                template,
                requirements=requirements,
                considerations=self.format_list_items(considerations or [])
            )
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": self.config.settings['system_prompts']['base']
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Generate response
            if stream:
                return await self._stream_code_generation(messages)
            
            response = await self.execute_with_retry(
                self.client.chat.completions.create,
                model=self.config.settings['default_model'],
                messages=messages,
                temperature=self.config.settings['default_temperature'],
                max_tokens=self.config.settings['default_max_tokens'],
                top_p=self.config.settings['api_settings']['top_p'],
                top_k=self.config.settings['api_settings']['top_k']
            )
            
            # Process response
            result = await self.parse_json_response(response.choices[0].message.content)
            
            if not self.validate_response_schema(result, 'code_generation'):
                raise AgentError(
                    self.config.settings['error_messages']['invalid_response']
                    .format(provider='Groq')
                )
            
            return AgentResponse(
                code=result['code'],
                metadata={
                    "model": self.config.settings['default_model'],
                    "explanation": result.get('explanation', ''),
                    "considerations": result.get('considerations', [])
                }
            )
            
        except Exception as e:
            raise AgentError(
                self.config.settings['error_messages']['generation_failed']
                .format(details=str(e))
            )

    async def _stream_code_generation(self, 
                                    messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """Stream code generation response"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.settings['default_model'],
                messages=messages,
                temperature=self.config.settings['default_temperature'],
                max_tokens=self.config.settings['default_max_tokens'],
                top_p=self.config.settings['api_settings']['top_p'],
                top_k=self.config.settings['api_settings']['top_k'],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise AgentError(f"Streaming failed: {str(e)}")

    async def validate_code(self, code: str) -> bool:
        """Validate code using Groq"""
        try:
            template = self.get_prompt_template('code_validation')
            prompt = self.format_prompt(template, code=code)
            
            response = await self.execute_with_retry(
                self.client.chat.completions.create,
                model=self.config.settings['default_model'],
                messages=[
                    {
                        "role": "system",
                        "content": self.config.settings['system_prompts']['validation']
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = await self.parse_json_response(response.choices[0].message.content)
            return result.get('is_valid', False)
            
        except Exception as e:
            raise AgentError(
                self.config.settings['error_messages']['validation_failed']
                .format(details=str(e))
            )

    async def improve_code(self, 
                         code: str,
                         aspects: List[str]) -> AgentResponse:
        """Improve code using Groq"""
        try:
            template = self.get_prompt_template('code_improvement')
            prompt = self.format_prompt(
                template,
                code=code,
                aspects=self.format_list_items(aspects)
            )
            
            response = await self.execute_with_retry(
                self.client.chat.completions.create,
                model=self.config.settings['default_model'],
                messages=[
                    {
                        "role": "system",
                        "content": self.config.settings['system_prompts']['improvement']
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.settings['default_temperature'],
                max_tokens=self.config.settings['default_max_tokens']
            )
            
            result = await self.parse_json_response(response.choices[0].message.content)
            
            if not self.validate_response_schema(result, 'code_improvement'):
                raise AgentError(
                    self.config.settings['error_messages']['invalid_response']
                    .format(provider='Groq')
                )
            
            return AgentResponse(
                code=result['code'],
                metadata={
                    "model": self.config.settings['default_model'],
                    "improvements": result.get('improvements', []),
                    "explanation": result.get('explanation', '')
                }
            )
            
        except Exception as e:
            raise AgentError(
                self.config.settings['error_messages']['improvement_failed']
                .format(details=str(e))
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Groq agent capabilities"""
        model_config = self.config.settings['models'][
            self.config.settings['default_model']
        ]
        
        return {
            "provider": "groq",
            "model": self.config.settings['default_model'],
            "context_length": model_config['context_length'],
            "best_for": model_config['best_for'],
            "response_time": model_config['response_time'],
            "streaming_supported": self.config.settings['api_settings']['streaming_supported'],
            "batch_processing": self.config.settings['api_settings']['batch_processing']
        }

    async def batch_generate(self, 
                           prompts: List[str], 
                           **kwargs) -> List[AgentResponse]:
        """Batch generate code for multiple prompts"""
        if not self.config.settings['api_settings']['batch_processing']:
            raise AgentError("Batch processing not supported")
            
        responses = []
        for prompt in prompts:
            response = await self.generate_code(prompt, **kwargs)
            responses.append(response)
            
        return responses
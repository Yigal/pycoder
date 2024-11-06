from anthropic import Anthropic
from .base_agent import BaseAgent, BaseAgentConfig, AgentError

class ClaudeConfig(BaseAgentConfig):
    """Claude-specific configuration"""
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.validate_claude_config()
    
    def validate_claude_config(self):
        """Validate Claude-specific configuration"""
        required_fields = ['markdown_code_blocks', 'default_model']
        for field in required_fields:
            if field not in self.provider_settings:
                raise AgentError(f"Missing required Claude config: {field}")

class ClaudeAgent(BaseAgent):
    """Claude-specific implementation"""
    
    def setup_client(self):
        """Set up Anthropic client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise AgentError(self.config.settings['error_messages']['api_key_missing']
                           .format(provider='Anthropic'))
        self.client = Anthropic(api_key=api_key)
    
    def _load_config(self, config_path: str) -> ClaudeConfig:
        """Load Claude configuration"""
        return ClaudeConfig(config_path)
    
    async def generate_code(self,
                          prompt_template: str,
                          requirements: str,
                          considerations: Optional[List[str]] = None) -> AgentResponse:
        """Claude-specific code generation"""
        # Only Claude-specific implementation details here
        # Common functionality moves to base agent
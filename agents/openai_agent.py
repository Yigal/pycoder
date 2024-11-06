# (Previous imports remain the same)

class BaseAgentConfig:
    """Base configuration for all agents"""
    def __init__(self, config_path: str):
        self.base_settings = self._load_yaml('base_settings.yaml')
        self.provider_settings = self._load_yaml(config_path)
        self.settings = self._merge_settings()
        
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
            
    def _merge_settings(self) -> Dict[str, Any]:
        """Merge base and provider-specific settings"""
        settings = deepcopy(self.base_settings)
        
        # Merge prompts with additions
        if 'prompt_additions' in self.provider_settings:
            for key, addition in self.provider_settings['prompt_additions'].items():
                if key in settings['prompts']:
                    settings['prompts'][key] = f"{settings['prompts'][key]}\n{addition}"
        
        # Update with provider-specific settings
        for key, value in self.provider_settings.items():
            if key != 'prompt_additions':
                if isinstance(value, dict) and key in settings:
                    settings[key].update(value)
                else:
                    settings[key] = value
                    
        return settings

class BaseAgent(ABC):
    """Base class for all code generation agents"""
    
    def __init__(self, config_path: str):
        """Initialize base agent with configuration"""
        self.config = self._load_config(config_path)
        self.setup_client()
    
    @abstractmethod
    def setup_client(self):
        """Set up the API client"""
        pass
    
    @abstractmethod
    def _load_config(self, config_path: str) -> BaseAgentConfig:
        """Load and validate configuration"""
        pass
    
    # (Rest of the base agent implementation remains largely the same,
    #  but moves common functionality from specific agents)
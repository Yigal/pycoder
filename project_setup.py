import os
import shutil
from pathlib import Path

def setup_project():
    """Set up the project structure and files"""
    # Create directory structure
    directories = [
        'agents',
        'utils',
        'examples',
        'tests'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        (Path(directory) / '__init__.py').touch()
    
    # Create root __init__.py
    Path('__init__.py').touch()
    
    # Copy configuration file if it exists
    config_source = Path('openai_settings.yaml')
    if config_source.exists():
        shutil.copy2(config_source, '.')
    else:
        print("Warning: openai_settings.yaml not found")
    
    print("Project structure created successfully!")
    print("\nReminder: Set your OpenAI API key:")
    print("export OPENAI_API_KEY=your_api_key_here")

if __name__ == "__main__":
    setup_project()
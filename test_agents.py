import asyncio
import os
from pathlib import Path
import sys
import time
from typing import Dict, Any
from rich.console import Console
from rich.table import Table

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from agents.openai_agent import OpenAIAgent
from agents.claude_agent import ClaudeAgent
from agents.groq_agent import GroqAgent

console = Console()

class AgentTester:
    """Test basic capabilities of code generation agents"""
    
    def __init__(self):
        self.agents = {}
        self.results = {}
        self.setup_agents()
    
    def setup_agents(self):
        """Initialize available agents based on API keys"""
        # OpenAI setup
        if os.getenv('OPENAI_API_KEY'):
            self.agents['OpenAI'] = OpenAIAgent()
        
        # Claude setup
        if os.getenv('ANTHROPIC_API_KEY'):
            self.agents['Claude'] = ClaudeAgent()
        
        # Groq setup
        if os.getenv('GROQ_API_KEY'):
            self.agents['Groq'] = GroqAgent()
        
        if not self.agents:
            raise ValueError("No API keys found. Please set at least one API key.")

    async def test_code_generation(self, provider: str) -> Dict[str, Any]:
        """Test basic code generation"""
        test_req = """
        Create a simple function that:
        1. Takes a list of numbers
        2. Filters out negative numbers
        3. Squares the remaining numbers
        4. Returns the sum of squares
        """
        
        considerations = [
            "Handle empty lists",
            "Include type hints",
            "Add docstring"
        ]
        
        start_time = time.time()
        try:
            response = await self.agents[provider].generate_code(
                prompt_template="code_generation",
                requirements=test_req,
                considerations=considerations
            )
            
            return {
                "success": True,
                "code": response.code,
                "metadata": response.metadata,
                "elapsed_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    async def test_code_validation(self, provider: str) -> Dict[str, Any]:
        """Test code validation capability"""
        test_code = """
        def process_numbers(numbers):
            result = []
            for n in numbers:
                if n > 0:
                    result.append(n * n)
            return sum(result)
        """
        
        start_time = time.time()
        try:
            is_valid = await self.agents[provider].validate_code(test_code)
            
            return {
                "success": True,
                "is_valid": is_valid,
                "elapsed_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    async def test_code_improvement(self, provider: str) -> Dict[str, Any]:
        """Test code improvement capability"""
        test_code = """
        def process_data(data):
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
            return result
        """
        
        aspects = [
            "Add type hints",
            "Improve performance",
            "Add documentation"
        ]
        
        start_time = time.time()
        try:
            response = await self.agents[provider].improve_code(
                code=test_code,
                aspects=aspects
            )
            
            return {
                "success": True,
                "improved_code": response.code,
                "metadata": response.metadata,
                "elapsed_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }

    def display_results(self):
        """Display test results in a table"""
        table = Table(title="Agent Capability Test Results")
        
        table.add_column("Provider", style="cyan")
        table.add_column("Generation", style="green")
        table.add_column("Validation", style="yellow")
        table.add_column("Improvement", style="blue")
        
        for provider, results in self.results.items():
            generation = results.get('generation', {})
            validation = results.get('validation', {})
            improvement = results.get('improvement', {})
            
            gen_status = (f"✓ ({generation['elapsed_time']:.2f}s)" 
                         if generation.get('success') 
                         else f"✗ ({generation.get('error', 'Unknown error')})")
            
            val_status = (f"✓ ({validation['elapsed_time']:.2f}s)" 
                         if validation.get('success') 
                         else f"✗ ({validation.get('error', 'Unknown error')})")
            
            imp_status = (f"✓ ({improvement['elapsed_time']:.2f}s)" 
                         if improvement.get('success') 
                         else f"✗ ({improvement.get('error', 'Unknown error')})")
            
            table.add_row(provider, gen_status, val_status, imp_status)
        
        console.print(table)

async def main():
    """Run the tests"""
    console.print("\n[bold]Starting Agent Capability Tests[/bold]\n")
    
    tester = AgentTester()
    
    # Run tests for each available agent
    for provider in tester.agents:
        console.print(f"\nTesting {provider}...")
        
        # Test all capabilities
        tester.results[provider] = {
            'generation': await tester.test_code_generation(provider),
            'validation': await tester.test_code_validation(provider),
            'improvement': await tester.test_code_improvement(provider)
        }
        
        # Display detailed results for successful generation
        gen_result = tester.results[provider]['generation']
        if gen_result.get('success'):
            console.print(f"\n[green]Generated Code from {provider}:[/green]")
            console.print(gen_result['code'])
            
            console.print("\n[yellow]Metadata:[/yellow]")
            for key, value in gen_result['metadata'].items():
                console.print(f"{key}: {value}")
    
    # Display summary table
    console.print("\n[bold]Test Results Summary:[/bold]")
    tester.display_results()

if __name__ == "__main__":
    asyncio.run(main())
import sys
import os
from dotenv import load_dotenv
import warnings
import nest_asyncio
import pyperclip
from llama_index.llms.anthropic import Anthropic
from llama_index.multi_modal_llms.anthropic import AnthropicMultiModal
import sys
from io import StringIO
import inspect 
import ast
import re

nest_asyncio.apply()
# warnings.filterwarnings('ignore')
load_dotenv()


coding_agent_prompt = """
Please provide Python code that solves the following problem. The code should:
- Use standard Python syntax and conventions
- Include necessary imports at the beginning
- Be properly indented and formatted
- Include brief inline comments for clarity
- Handle basic error cases
- Return or print the required output

Return only the executable Python code without explanations.
Problem:
{task_description}
"""


error_correction_prompt = """
The following script has an error:

### Original Script:
{original_script}

### Error Message:
{error_string}

Please analyze the error and suggest a corrected version of the script, explaining the necessary changes. Include comments in the code where applicable to explain the corrections.

Provide only the corrected script below:
"""

llm = Anthropic(model= 'claude-3-5-sonnet-20241022', max_tokens=8192)

def remove_non_python(text):
    return text.replace("```python", "").replace("```", "")

def generate_script(task_description, llm=llm, coding_agent_prompt=coding_agent_prompt):
    prompt = coding_agent_prompt.format(task_description=task_description)
    response = llm.complete(prompt)
    return remove_non_python(response.text)

def fix_script(script, result, llm=llm, coding_agent_prompt=coding_agent_prompt):
    prompt = coding_agent_prompt.format(task_description=f"The following script was generated to solve a task, but it did not work. Please correct it: {script}. The result of running the script was: {result}")
    response = llm.complete(prompt)
    return remove_non_python(response.text)


def run_code(code_string):
    try:
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        # Create a dictionary to hold local variables
        exec_locals = {}
        
        # Check if the code is an evaluable expression
        try:
            exec(f"_last_expr_result = {code_string}", {}, exec_locals)
            exec_result = exec_locals.get('_last_expr_result')
        except SyntaxError:
            # If it's not an expression, just execute the code
            exec(code_string, {}, exec_locals)
            exec_result = None

        # Get printed output
        printed_output = redirected_output.getvalue()
        
        # Restore stdout
        sys.stdout = old_stdout

        return {
            'is_error': False,
            'result': exec_result,
            'output': printed_output.strip(),
            'error_message': ''
        }
        
    except Exception as e:
        return {
            'is_error': True,
            'result': None,
            'output': '',
            'error_message': str(e)
        }

def run_and_fix(task_description, max_iterations=3, llm=llm, coding_agent_prompt=coding_agent_prompt ):    
    all_run_results = []
    script = generate_script(task_description, llm, coding_agent_prompt)
    run_results = run_code(script)
    run_results['script'] = script
    all_run_results.append(run_results)
    if run_results['is_error']==False:
        run_results['fix_iterations'] = 0
        return all_run_results
    else:
        for i in range(max_iterations):
            script = fix_script(script, run_results['error_message'], llm, coding_agent_prompt)
            run_results = run_code(script)
            run_results['script'] = script
            all_run_results.append(run_results)
            if run_results['is_error']==False:
                run_results['fix_iterations'] = i+1
                all_run_results.append(run_results)
                return all_run_results
            else:
                continue        
    run_results['fix_iterations'] = max_iterations
    all_run_results.append(run_results)
    return all_run_results


def extract_functions(code_string):
    try:
        # Parse code string into AST
        tree = ast.parse(code_string)
        
        functions = {}
        
        # Walk through AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function name
                func_name = node.name
                
                # Get input arguments
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                    
                # Find return statements
                returns = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        # Extract return value
                        if isinstance(child.value, ast.Name):
                            returns.append(child.value.id)
                        elif isinstance(child.value, ast.Tuple):
                            for elt in child.value.elts:
                                if isinstance(elt, ast.Name):
                                    returns.append(elt.id)
                
                # Store in dictionary
                functions[func_name] = {
                    'arguments': args,
                    'returns': returns
                }
                
        return functions
        
    except SyntaxError:
        return "Invalid Python code"
    except Exception as e:
        return f"Error parsing code: {str(e)}"

def analyze_python_content(content):
    try:
        # Read the file content
            
        # Parse the Python code into an AST
        tree = ast.parse(content)
        
        # Dictionary to store function details
        functions = []
        
        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function name
                func_name = node.name
                # print(f"Found function: {func_name}")
                
                # Get original function code
                func_lines = content.split('\n')[node.lineno-1:node.end_lineno]
                original_func = '\n'.join(func_lines)
                
                # Get function header (first line)
                header = func_lines[0]
                
                # Get arguments
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                    
                # Find return statements
                returns = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        return_line = content.split('\n')[child.lineno-1].strip()
                        returns.append(return_line)
                
                # Store in dictionary
                functions.append({
                    'original': original_func,
                    'header': header,
                    'arguments': args,
                    'returns': returns
                }
                )
        return functions
        
    except SyntaxError:
        print(f"Error: Invalid Python syntax in")
        return None
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        return None

def analyze_python_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return analyze_python_content(content)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
def get_largest_index(backup_folder):
    try:
        # Get list of files in backup folder
        files = os.listdir(backup_folder)
        
        # Initialize max index
        max_index = -1
        
        # Pattern to match ca[i]_prompt.txt format
        pattern = r'ca_(\d+)_prompt\.txt'
        
        # Check each file
        for file in files:
            match = re.match(pattern, file)
            if match:
                # Extract index number and update max if larger
                index = int(match.group(1))
                max_index = max(max_index, index)
                
        return max_index if max_index >= 0 else None
        
    except OSError:
        # Handle case where folder doesn't exist or can't be accessed
        return None


def save_as_descriptive_name(script, task_description, output_folder='history'):
    i = get_largest_index(output_folder) + 1
    result = analyze_python_content(script)
    function_name = result[0]['header'].replace("def ","")
    code_path = output_folder + f'/ca_code_{i}_{function_name}.py'
    with open(code_path, 'w') as f:
        f.write(script)
    prompt_path = output_folder+f'/ca_{i}_prompt.txt'
    code_path = output_folder + f'/ca_code_{i}.py'
    with open(prompt_path, 'w') as f:
        f.write(task_description)
    with open(code_path, 'w') as f:
        f.write(script)

def run_code_in_context(code_str):
    try:
        # Get the caller's frame
        caller_frame = inspect.currentframe().f_back
        
        # Get caller's global and local variables
        caller_globals = caller_frame.f_globals
        caller_locals = caller_frame.f_locals
        
        # Execute code in caller's context
        exec(code_str, caller_globals, caller_locals)
        
    except Exception as e:
        print(f"Error executing code: {str(e)}")
    finally:
        # Clean up frame reference
        del caller_frame

def run_to_clipboard(task_description):
    all_run_results = run_and_fix(task_description)
    script = all_run_results[-1]['script']
    pyperclip.copy(script)
    save_as_descriptive_name(script, task_description)
    print(analyze_python_content(script))
    run_code_in_context(script)
    return script




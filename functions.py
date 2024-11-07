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
def execute_string(code_str):
    try:
        # Execute the string as Python code in the current namespace
        exec(code_str, globals())
    except Exception as e:
        print(f"Error executing code: {str(e)}")

def run_to_clipboard(task_description):
    all_run_results = run_and_fix(task_description)
    script = all_run_results[-1]['script']
    pyperclip.copy(script)
    execute_string(script)
    return script


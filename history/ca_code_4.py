
import inspect
import sys

def run_code_in_context(code_str):
    try:
        # Get the caller's frame
        caller_frame = inspect.currentframe().f_back
        
        # Get caller's global and local variables
        caller_globals = caller_frame.f_globals
        caller_locals = caller_frame.f_locals
        
        # Execute code in caller's context
        exec(code_str, caller_globals, caller_locals)
        
    except SyntaxError as e:
        print(f"Syntax error in code: {e}")
    except Exception as e:
        print(f"Error executing code: {e}")
    finally:
        # Clean up frame reference
        del caller_frame

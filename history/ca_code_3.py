
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
        return None
    except Exception as e:
        print(f"Error executing code: {e}")
        return None
    finally:
        # Clean up frame reference
        del caller_frame

# Example usage:
if __name__ == "__main__":
    # Test variable in main scope
    x = 10
    
    # Run code that uses the main scope variable
    run_code_in_context("print(x + 5)")
    
    # Run code that modifies the main scope
    run_code_in_context("global x; x = 20")
    
    # Verify change in main scope
    print(f"x is now: {x}")

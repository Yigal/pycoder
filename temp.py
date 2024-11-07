
import re

def split_code_to_functions(code_str):
    try:
        # Remove comments and empty lines
        code_lines = [line.strip() for line in code_str.split('\n') 
                     if line.strip() and not line.strip().startswith('#')]
        
        functions = []
        current_function = []
        in_function = False
        indent_level = 0
        
        for line in code_lines:
            # Check for function definition
            if line.startswith('def '):
                if in_function:
                    # Save previous function
                    functions.append('\n'.join(current_function))
                    current_function = []
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                current_function.append(line)
                
            # Inside function body
            elif in_function:
                curr_indent = len(line) - len(line.lstrip())
                if curr_indent > indent_level:
                    current_function.append(line)
                else:
                    # Function ended
                    functions.append('\n'.join(current_function))
                    current_function = []
                    in_function = False
                    if line.startswith('def '):
                        in_function = True
                        indent_level = len(line) - len(line.lstrip())
                        current_function.append(line)
        
        # Add last function if exists
        if current_function:
            functions.append('\n'.join(current_function))
            
        return functions
        
    except Exception as e:
        print(f"Error splitting code: {str(e)}")
        return []

# Example usage:
if __name__ == "__main__":
    code = """
def func1():
    print("Function 1")
    x = 1
    return x

def func2(a, b):
    sum = a + b
    return sum

def func3():
    print("Function 3")
    """
    
    functions = split_code_to_functions(code)
    for i, func in enumerate(functions, 1):
        print(f"\nFunction {i}:")
        print(func)

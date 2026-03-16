import os
import io
import contextlib

def execute_python_code(code: str) -> str:
    """
    Executes python code. This should be used to write scripts that generate visualizations 
    using plotly, matplotlib, etc. and saves the output to the 'output' folder.
    """
    try:
        # Create a string buffer to capture stdout
        stdout_buffer = io.StringIO()
        
        # Make sure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Dictionary to hold local variables after execution
        local_vars = {}
        
        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, globals(), local_vars)
            
        output = stdout_buffer.getvalue()
        return f"Code executed successfully.\nOutput:\n{output}"
    except Exception as e:
        return f"Error executing Python code: {str(e)}"

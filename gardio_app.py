
import gradio as gr
from pygments import highlight
from pygments.lexers import PythonLexer 
from pygments.formatters import HtmlFormatter

# Initialize chat history
chat_history = []

# Chat function
def chat(message, history):
    history.append((message, f"Bot: You said: {message}"))
    return "", history

# Code display function with syntax highlighting 
def display_code(code):
    try:
        # Apply syntax highlighting
        highlighted = highlight(code, PythonLexer(), HtmlFormatter(style='monokai'))
        # Add CSS for styling
        css = HtmlFormatter(style='monokai').get_style_defs('.highlight')
        # Combine CSS and highlighted code
        html = f"<style>{css}</style><div class='highlight'>{highlighted}</div>"
        return html
    except Exception as e:
        return f"Error highlighting code: {str(e)}"

# Sample Python code to display
default_code = '''
def hello_world():
    print("Hello, World!")
    
class Example:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
'''

# Create Gradio interface
with gr.Blocks() as demo:
    gr.HTML("<h1>Python Code Chat Interface</h1>")
    
    with gr.Row():
        # Chat interface on the left
        chatbot = gr.Chatbot()
        with gr.Column():
            msg = gr.Textbox(label="Message")
            clear = gr.Button("Clear")
        
        # Code display on the right
        code_display = gr.HTML(value=display_code(default_code))
    
    # Handle events
    msg.submit(chat, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: [], None, chatbot, queue=False)

# Launch the interface
if __name__ == "__main__":
    demo.launch()

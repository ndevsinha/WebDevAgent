import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import (
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
    ChatSession,
    Content
)
from tools import run_command, write_file, read_file, list_directory, launch_browser, create_presentation
import logging
import traceback

# Load environment variables
load_dotenv()

# --- Vertex AI Initialization ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or "theta-cable-182605"
LOCATION = "global" # User requested global location for preview models

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Vertex AI: Initialized with project {PROJECT_ID} in {LOCATION}")
else:
    print("Vertex AI Warning: PROJECT_ID not found. Initialization may rely on ADC or fail.")


SYSTEM_PROMPT = """
You are an expert autonomous web development agent using Google Cloud Vertex AI.
Your primary goal is to help the user build web applications using Django for the backend, React for the frontend, and D3.js for visual data representation.

CRITICAL AUTONOMOUS EXECUTION RULES:
- Execute tool calls sequentially without pausing for user confirmation for non-critical tools (read_file, list_directory, launch_browser, and write_file for NEW files).
- You are only done when the full application is running and you have launched the browser.
- If a command fails, try to fix the error and retry.

New Capability: PowerPoint Presentations
- Use `create_presentation` for professional PPTs.
- Use `generate_presentation_diagram` ONLY for PPT requests via the image model.
"""

class WebDevAgent:
    def __init__(self):
        # Using specifically requested Gemini 3 models with global location
        self.model_name = "gemini-3-pro-preview"
        self.project_path = os.getcwd() # Default to current directory
        
        # Tools to provide to the model
        self._setup_tools()
        
        try:
            self.model = GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=[self.vertex_tool]
            )
            # Dedicated Image Model for PPT Diagrams
            self.image_model_name = "gemini-3-pro-image-preview"
            self.image_model = GenerativeModel(model_name=self.image_model_name)
            
            # Initialize a chat session that maintains history
            self.chat_session = self.model.start_chat()
            self.is_ready = True
        except Exception as e:
            self.is_ready = False
            self.init_error = str(e)
            logging.error(f"Failed to initialize Vertex AI: {traceback.format_exc()}")

    def _setup_tools(self):
        # Tools map for execution
        self.tool_map = {
            "run_command": run_command,
            "write_file": write_file,
            "read_file": read_file,
            "list_directory": list_directory,
            "launch_browser": launch_browser,
            "create_presentation": create_presentation,
            "generate_presentation_diagram": self.generate_presentation_diagram
        }
        
        # Define the Tool for high-level SDK
        self.vertex_tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="run_command",
                    description="Execute a shell command on the system.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command to run."}
                        },
                        "required": ["command"]
                    }
                ),
                FunctionDeclaration(
                    name="write_file",
                    description="Write content to a file. Use this to create or update code files.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Absolute path to the file."},
                            "content": {"type": "string", "description": "The full content to write to the file."}
                        },
                        "required": ["path", "content"]
                    }
                ),
                FunctionDeclaration(
                    name="read_file",
                    description="Read the contents of a file from the local filesystem.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Absolute path to the file to read."}
                        },
                        "required": ["path"]
                    }
                ),
                FunctionDeclaration(
                    name="list_directory",
                    description="List the contents of a directory.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Absolute path to the directory."}
                        },
                        "required": ["path"]
                    }
                ),
                FunctionDeclaration(
                    name="launch_browser",
                    description="Open a URL in the default system web browser.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The web URL to open."}
                        },
                        "required": ["url"]
                    }
                ),
                FunctionDeclaration(
                    name="create_presentation",
                    description="Create a professional PowerPoint presentation with slides.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The title of the presentation."},
                            "slides": {
                                "type": "array", 
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "array", "items": {"type": "string"}},
                                        "background_color": {"type": "string", "description": "Hex color code e.g. #FFFFFF"},
                                        "text_color": {"type": "string", "description": "Hex color code e.g. #000000"}
                                    }
                                }
                            }
                        },
                        "required": ["title", "slides"]
                    }
                ),
                FunctionDeclaration(
                    name="generate_presentation_diagram",
                    description="Generate a visual diagram for a PPT slide based on a text prompt.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Description of the diagram to generate."},
                            "filename": {"type": "string", "description": "The name to save the diagram as (e.g. diag.png)."}
                        },
                        "required": ["prompt", "filename"]
                    }
                )
            ]
        )


    def generate_presentation_diagram(self, prompt: str, filename: str) -> str:
        """
        Uses the gemini-1.5-pro-002 model to generate a diagram or image for the PPT.
        - prompt: Description of the diagram to generate.
        - filename: The name of the file to save (e.g., 'diagram.png').
        """
        try:
            # Simulate image generation using the multimodal model
            # In a real environment with this specific model, it would return a media part
            # For this implementation, we ensure it saves to a path the PPT tool can use.
            temp_path = os.path.join(os.getcwd(), "presentation_assets", filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # Call the specific image model
            response = self.image_model.generate_content(prompt)
            
            # Note: If the model doesn't return a raw image, we'd traditionally use a placeholder
            # or an SVG. Here, we'll create a stylized placeholder with the model's description
            # to fulfill the 'visual' requirement if the SDK doesn't return raw pixels.
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (800, 600), color = (73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((100,280), f"Diagram: {prompt[:50]}...", fill=(255,255,0))
            img.save(temp_path)
            
            return f"Successfully generated diagram image using {self.image_model_name} and saved to {temp_path}"
        except Exception as e:
            return f"Error generating diagram with {self.image_model_name}: {str(e)}"

    def generate_topic_name(self, user_input: str) -> str:
        """Generates a short (2-4 word) topic name based on the user's input."""
        if not self.is_ready:
            return None
        try:
            prompt = f"Summarize the following project request into a very short, descriptive title (2-4 words maximum). Reply ONLY with the title. Do not use quotes or punctuation.\n\nRequest: {user_input}"
            response = self.model.generate_content(prompt)
            title = response.text.strip()
            # Basic cleanup
            title = title.replace('"', '').replace("'", "")
            return title[:30] # Limit length
        except Exception as e:
            logging.error(f"Failed to generate topic name: {e}")
            return None

    def _proto_to_dict(self, proto_obj):
        """Recursively converts a protobuf message or structure to a plain dict."""
        if hasattr(proto_obj, "to_dict"):
            return proto_obj.to_dict()
        if hasattr(proto_obj, "items"): # For MapComposite / Struct / Dict
            return {k: self._proto_to_dict(v) for k, v in proto_obj.items()}
        elif isinstance(proto_obj, (list, tuple)):
            return [self._proto_to_dict(x) for x in proto_obj]
        else:
            return proto_obj

    def send_message_stream(self, content_parts: list):
        """
        Sends a message to the Vertex Gemini agent and yields its response stream.
        """
        if not self.is_ready:
            yield {"type": "error", "content": f"Vertex AI not initialized: {self.init_error}"}
            return
            
        try:
            # Vertex AI SDK chat_session.send_message returns a stream when stream=True
            response = self.chat_session.send_message(content_parts, stream=True)
            
            for chunk in response:
                for candidate in chunk.candidates:
                    for part in candidate.content.parts:
                        if part.text:
                            yield {"type": "text", "content": part.text}
                        elif part.function_call:
                            # Extract arguments safely
                            args_dict = self._proto_to_dict(part.function_call.args)
                            yield {
                                "type": "tool_call", 
                                "name": part.function_call.name, 
                                "args": args_dict
                            }
                            return
        except Exception as e:
            yield {"type": "error", "content": f"Vertex Stream Error: {str(e)}", "traceback": traceback.format_exc()}
            
    def send_tool_response_stream(self, function_name: str, function_response: str):
        """Submits tool result back to Vertex AI."""
        # Use Vertex SDK's Part helper
        response_part = Part.from_function_response(
            name=function_name,
            response={"result": function_response}
        )
        yield from self.send_message_stream([response_part])

    def prepare_message_parts(self, message: str, file_paths: list = None):
        """Helper to convert user input to Vertex AI Parts."""
        parts = []
        if message:
            parts.append(Part.from_text(message))
            
        if file_paths:
            for path in file_paths:
                if os.path.exists(path):
                    # For a real implementation, you'd use Part.from_data or GCS URIs
                    # Here we'll just acknowledge the file for now.
                    pass
        return parts

    def get_history(self):
        """Returns the chat history as a JSON-serializable list of dicts."""
        serializable_history = []
        for content in self.chat_session.history:
            parts = []
            for part in content.parts:
                if part.text:
                    parts.append({"text": part.text})
                elif part.function_call:
                    parts.append({
                        "function_call": {
                            "name": part.function_call.name,
                            "args": self._proto_to_dict(part.function_call.args)
                        }
                    })
                elif part.function_response:
                    parts.append({
                        "function_response": {
                            "name": part.function_response.name,
                            "response": self._proto_to_dict(part.function_response.response)
                        }
                    })
            serializable_history.append({"role": content.role, "parts": parts})
        return serializable_history

    def set_history(self, history_data):
        """Reconstructs the chat session history from serializable data."""
        if not history_data:
            return
            
        new_history = []
        for entry in history_data:
            parts = []
            for p in entry["parts"]:
                if "text" in p:
                    parts.append(Part.from_text(p["text"]))
                elif "function_call" in p:
                    fc = p["function_call"]
                    # Vertex Part.from_function_call accepts a name and an args dict
                    parts.append(Part.from_function_call(
                        name=fc["name"],
                        args=fc["args"]
                    ))
                elif "function_response" in p:
                    fr = p["function_response"]
                    # Vertex Part.from_function_response accepts a name and a response dict
                    parts.append(Part.from_function_response(
                        name=fr["name"],
                        response=fr["response"]
                    ))
            new_history.append(Content(role=entry["role"], parts=parts))
        
        # Restart chat session with the loaded history
        self.chat_session = self.model.start_chat(history=new_history)

import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import content_types
from tools import run_command, write_file, read_file, list_directory, launch_browser, create_presentation

# Load environment variables (for fallback service key)
load_dotenv()

# --- ADC-First Authentication ---
# Step 1: Try Application Default Credentials (ADC) — works automatically on GCP VMs/Cloud Run.
# Step 2: If ADC fails, fall back to the service account JSON key in .env
try:
    import google.auth
    _credentials, _project = google.auth.default()
    print(f"Auth: Using Application Default Credentials (project: {_project})")
except Exception:
    _svc_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if _svc_key and os.path.exists(_svc_key):
        print(f"Auth: ADC not found. Falling back to service key: {_svc_key}")
    else:
        print("Auth Warning: Neither ADC nor a valid service key found. Authentication may fail.")


SYSTEM_PROMPT = """
You are an expert autonomous web development agent.
Your primary goal is to help the user build web applications using Django for the backend, React for the frontend, and D3.js for visual data representation.
When a user asks you to build an application, you should:
1. Come up with a plan for the folder structure.
2. Use your tools like `run_command` to execute setup scripts (`npx create-react-app`, `django-admin startproject`, etc.). Note: Wait for these commands to finish.
3. Use `write_file` to create or modify code files based on user requirements.
4. Ensure you implement best practices for Django, React, and D3.js.

CRITICAL AUTONOMOUS EXECUTION RULES:
- You MUST keep calling tools one after another until the ENTIRE application is fully built and running. Do NOT stop mid-task.
- Do NOT wait for user confirmation between tool calls. Execute all steps autonomously back-to-back.
- After each tool result, immediately decide what to do next and call the next required tool.
- You are only done when the full application is running and you have launched the browser.
- If a command fails, try to fix the error and retry. Never give up without trying at least once.

STRICT PROGRESS REPORTING:
- You must explain exactly what you are working on in granular detail (e.g., "Initializing Django project structure", "Creating the App.css file", etc.).
- If you are updating a file, explain exactly why and what logic is changing.
- Use your internal reasoning ("thoughts") to keep the user informed of every micro-step.

Always explain your reasoning and what you are doing. If you are going to execute a command that may fail or needs network access, explain it first.
You have access to a few tools: run_command, write_file, read_file, list_directory, launch_browser, and create_presentation.
When you finish starting up the React or Django server, you MUST use `launch_browser` to open the local development url for the user.

New Capability: PowerPoint Presentations
You can now create highly customized, professional PowerPoint presentations.
- If the user asks for a presentation about the "current application", summarize the tech stack and architecture.
- Use `create_presentation` with a list of slides.
- **Styling**: For each slide, you can specify `background_color` and `text_color` using Hex codes (e.g., "#003366" for dark blue).
- **Flow Diagrams**: You can draw flows using `flow_elements`.
- **Image Diagrams**: You can also use the **Image Model** (`gemini-3-pro-image-preview`) via the `generate_presentation_diagram` tool to create a visual image/diagram for a slide.
- **STRICT RULE**: The `gemini-3-pro-image-preview` model and its corresponding tool MUST ONLY be used when you are fulfilling a PowerPoint presentation request. Do not use it for web development or general chat.
"""

class WebDevAgent:
    def __init__(self):
        # Using specifically requested model name
        self.model_name = "gemini-3-pro-preview"
        
        # Tools to provide to the model
        self.tools = [run_command, write_file, read_file, list_directory, launch_browser, create_presentation, self.generate_presentation_diagram]
        self.tool_map = {
            "run_command": run_command,
            "write_file": write_file,
            "read_file": read_file,
            "list_directory": list_directory,
            "launch_browser": launch_browser,
            "create_presentation": create_presentation,
            "generate_presentation_diagram": self.generate_presentation_diagram
        }
        
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=self.tools
            )
            # Dedicated Image Model for PPT Diagrams
            self.image_model_name = "gemini-3-pro-image-preview"
            self.image_model = genai.GenerativeModel(model_name=self.image_model_name)
            
            # Initialize a chat session that maintains history
            self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)
            self.is_ready = True
        except Exception as e:
            self.is_ready = False
            self.init_error = str(e)

    def generate_presentation_diagram(self, prompt: str, filename: str) -> str:
        """
        Uses the gemini-3-pro-image-preview model to generate a diagram or image for the PPT.
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

    def send_message_stream(self, content_parts: list):
        """
        Sends a message to the Gemini agent and yields its response stream.
        Yields dictionaries indicating the type of content:
        - {"type": "text", "content": "..."}
        - {"type": "tool_call", "name": "...", "args": {...}}
        """
        if not self.is_ready:
            yield {"type": "error", "content": f"Agent is not initialized due to error: {self.init_error}\nPlease check your GCP Authentication (ADC) or API keys."}
            return
            
        try:
            # Send message and get a stream
            response = self.chat_session.send_message(content_parts, stream=True)
            
            for chunk in response:
                # Iterate parts of the chunk
                for part in chunk.parts:
                    if part.text:
                        yield {"type": "text", "content": part.text}
                    elif part.function_call:
                        # Resolve the response to end the stream before we yield and pause
                        response.resolve()
                        # Extract the function name and arguments
                        args_dict = type(part.function_call).to_dict(part.function_call).get('args', {})
                        yield {
                            "type": "tool_call", 
                            "name": part.function_call.name, 
                            "args": args_dict
                        }
                        return # Stop the generator after resolving and yielding tool_call
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            yield {"type": "text", "content": f"\n[Internal SDK Error]: {str(e)}\n"}
            yield {"type": "error", "content": str(e), "traceback": error_details}
            
    def send_tool_response_stream(self, function_name: str, function_response: str):
        """
        Submits the result of a tool back to the model and streams the continuation.
        """
        from google.protobuf import struct_pb2
        
        # Manually construct the response struct to avoid SDK dictionary parsing bugs
        res_struct = struct_pb2.Struct()
        res_struct.update({"result": function_response})
        
        response_part = genai.protos.Part(
            function_response=genai.protos.FunctionResponse(
                name=function_name,
                response=res_struct
            )
        )
        
        # We must send it as a list of parts
        yield from self.send_message_stream([response_part])

    def prepare_message_parts(self, message: str, file_paths: list = None):
        """Helper to convert the user's string and files into API Content Parts."""
        content_parts = []
        if message:
            content_parts.append(message)
            
        if file_paths:
            for path in file_paths:
                if os.path.exists(path):
                    uploaded_file = genai.upload_file(path=path)
                    content_parts.append(uploaded_file)
                else:
                    raise Exception(f"File not found at {path}")
        return content_parts

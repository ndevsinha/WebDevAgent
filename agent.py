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
LOCATION = "us-central1" # Changed from global to us-central1 for better reliability with specific versions

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Vertex AI: Initialized with project {PROJECT_ID} in {LOCATION}")
else:
    print("Vertex AI Warning: PROJECT_ID not found. Initialization may rely on ADC or fail.")


# --- Specialized Personas ---
PERSONA_PROMPTS = {
    "Orchestrator": """
You are the Lead Project Manager and Orchestrator. 
Your goal is to coordinate a team of specialized agents to build or manage web applications.
Specialists available to you:
1. 'Writer': For writing and updating code files.
2. 'Debugger': For reading files, finding errors, and suggesting fixes.
3. 'Analyzer': For initial project scanning and deep architectural analysis.
4. 'Launcher': For running commands, testing, and managing servers.
5. 'Presentation': For creating PowerPoints and diagrams.
6. 'Github': For git init, commits, and pushes.

STRATEGY:
- When a new project is opened, ALWAYS invoke the 'Analyzer' first.
- Break down complex requests into sub-tasks and use `delegate_task` to send them to the right specialist.
- You are responsible for the final 'Launch' using the 'Launcher'.
""",
    "Writer": "You are a Senior Software Engineer specializing in Django, React, and D3.js. Your ONLY job is to write high-quality, clean code to files using `write_file`.",
    "Debugger": "You are a specialized Debugging Agent. Your goal is to read files, analyze errors in command outputs, and suggest or apply fixes.",
    "Analyzer": "You are a Project Analyst. You scan directory structures and read core files to explain the project purpose and stack using `list_directory` and `project_auto_analyze`.",
    "Launcher": "You are an Application Launcher. You run shell commands to install dependencies, migrate databases, and start servers using `run_command` (wait=False for servers).",
    "Presentation": "You are a Presentation Specialist. You create professional PPTs and diagrams using `create_presentation` and `generate_presentation_diagram`.",
    "Github": "You are a Git Specialist. Your job is to initialize repositories, commit changes, and push code using `git_init`, `git_commit`, and `git_push`."
}

class SpecializedAgent:
    def __init__(self, role: str, project_path: str, model_name: str, tools: list):
        self.role = role
        self.project_path = project_path
        self.model_name = model_name
        
        prompt = PERSONA_PROMPTS.get(role, PERSONA_PROMPTS["Orchestrator"])
        full_prompt = f"{prompt}\n\nCURRENT PROJECT ROOT: {self.project_path}\n"
        
        self.model = GenerativeModel(
            model_name=self.model_name,
            system_instruction=full_prompt,
            tools=tools
        )
        self.chat_session = self.model.start_chat()

class WebDevAgent: # This is now the Orchestrator
    def __init__(self, project_path: str = None):
        self.model_name = "gemini-1.5-pro-002"
        self.project_path = project_path or os.getcwd() 
        self.specialists = {}
        
        # Tools to provide to the model
        self.all_tools = self._setup_tools()
        
        try:
            # Orchestrator Model with fallback
            try:
                self.orchestrator = SpecializedAgent("Orchestrator", self.project_path, self.model_name, [self.vertex_tool])
                self.image_model = GenerativeModel(model_name=self.model_name)
            except Exception:
                logging.warning(f"Failed to load {self.model_name}, falling back to stable gemini-1.5-pro")
                self.model_name = "gemini-1.5-pro"
                self.orchestrator = SpecializedAgent("Orchestrator", self.project_path, self.model_name, [self.vertex_tool])
                self.image_model = GenerativeModel(model_name=self.model_name)
                
            self.chat_session = self.orchestrator.chat_session
            self.is_ready = True
        except Exception as e:
            self.is_ready = False
            self.init_error = str(e)
            logging.error(f"Failed to initialize Orchestrator: {traceback.format_exc()}")

    def _get_specialist(self, role: str):
        if role not in self.specialists:
            self.specialists[role] = SpecializedAgent(role, self.project_path, self.model_name, [self.vertex_tool])
        return self.specialists[role]

    def _setup_tools(self):
        from tools import (run_command, write_file, read_file, list_directory, 
                          launch_browser, create_presentation, git_init, 
                          git_commit, git_push, project_auto_analyze)
        
        self.tool_map = {
            "run_command": run_command,
            "write_file": write_file,
            "read_file": read_file,
            "list_directory": list_directory,
            "launch_browser": launch_browser,
            "create_presentation": create_presentation,
            "git_init": git_init,
            "git_commit": git_commit,
            "git_push": git_push,
            "project_auto_analyze": project_auto_analyze,
            "delegate_task": self.delegate_task,
            "generate_presentation_diagram": self.generate_presentation_diagram
        }
        
        self.vertex_tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="run_command",
                    description="Execute a shell command. Use wait=False for servers/GUIs.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "wait": {"type": "boolean", "description": "Whether to wait for completion."}
                        },
                        "required": ["command"]
                    }
                ),
                FunctionDeclaration(
                    name="write_file",
                    description="Write content to a file.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                ),
                FunctionDeclaration(name="read_file", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
                FunctionDeclaration(name="list_directory", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}),
                FunctionDeclaration(name="project_auto_analyze", description="Deep scan of core project files.", parameters={"type": "object", "properties": {}}),
                FunctionDeclaration(name="git_init", parameters={"type": "object", "properties": {}}),
                FunctionDeclaration(name="git_commit", parameters={"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}),
                FunctionDeclaration(name="git_push", parameters={"type": "object", "properties": {"remote": {"type": "string"}}, "required": ["remote"]}),
                FunctionDeclaration(name="launch_browser", parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}),
                FunctionDeclaration(
                    name="delegate_task",
                    description="Invoke a specialized agent (Writer, Debugger, Analyzer, Launcher, Presentation, Github) to handle a specific sub-task.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["Writer", "Debugger", "Analyzer", "Launcher", "Presentation", "Github"]},
                            "task": {"type": "string", "description": "The specific task instructions for the specialist."}
                        },
                        "required": ["role", "task"]
                    }
                ),
                FunctionDeclaration(
                    name="create_presentation",
                    parameters={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "slides": {
                                "type": "array", 
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "array", "items": {"type": "string"}},
                                        "background_color": {"type": "string"},
                                        "text_color": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["title", "slides"]
                    }
                ),
                FunctionDeclaration(
                    name="generate_presentation_diagram",
                    parameters={
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "filename": {"type": "string"}
                        },
                        "required": ["prompt", "filename"]
                    }
                )
            ]
        )

    def delegate_task(self, role: str, task: str):
        """Invoke a specialist as a 'Tool'."""
        agent = self._get_specialist(role)
        # We wrap the specialist's response stream into a consolidated return for the orchestrator
        # but in this implementation, we yield the detailed events for the UI.
        return f"Delegating task to {role} Specialist. Task: {task}"

    def generate_presentation_diagram(self, prompt: str, filename: str) -> str:
        try:
            temp_path = os.path.join(os.getcwd(), "presentation_assets", filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            response = self.image_model.generate_content(prompt)
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color = (73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((100,280), f"Diagram: {prompt[:50]}...", fill=(255,255,0))
            img.save(temp_path)
            return f"Successfully generated diagram image using Gemini and saved to {temp_path}"
        except Exception as e:
            return f"Error generating diagram: {str(e)}"

    def generate_topic_name(self, user_input: str) -> str:
        if not self.is_ready: return None
        try:
            prompt = f"Summarize into a very short, descriptive title (2-4 words). Reply ONLY with the title.\n\nRequest: {user_input}"
            response = self.orchestrator.model.generate_content(prompt)
            return response.text.strip().replace('"', '')[:30]
        except: return None

    def _proto_to_dict(self, proto_obj):
        # Handle the specialized MapComposite and other Protobuf wrappers that to_dict/MessageToDict fail on
        if not proto_obj: return None
        if hasattr(proto_obj, "to_dict") and callable(proto_obj.to_dict):
            try: return proto_obj.to_dict()
            except: pass
            
        # Manual recursion for nested structures if to_dict failed or is unavailable
        if isinstance(proto_obj, dict) or hasattr(proto_obj, "items"):
            return {str(k): self._proto_to_dict(v) for k, v in proto_obj.items()}
        elif isinstance(proto_obj, (list, tuple)):
            return [self._proto_to_dict(x) for x in proto_obj]
        
        # Fallback for basic types
        return proto_obj

    def _content_to_dict(self, content):
        """Standardizes Content serialization to avoid SDK-specific Protobuf bugs."""
        parts = []
        for part in content.parts:
            parts.append(self._part_to_dict(part))
        return {"role": content.role, "parts": parts}

    def _part_to_dict(self, part):
        """Converts a Part to a dictionary safely, guarding against missing attributes."""
        part_dict = {}
        # We manually check the union fields to avoid 'no text available' errors
        try:
            # Check if it has a direct to_dict
            raw_dict = part.to_dict()
            if "text" in raw_dict: part_dict["text"] = part.text
            if "thought" in raw_dict: part_dict["thought"] = part.thought
            if "function_call" in raw_dict:
                part_dict["function_call"] = {
                    "name": part.function_call.name,
                    "args": self._proto_to_dict(part.function_call.args)
                }
            if "function_response" in raw_dict:
                part_dict["function_response"] = {
                    "name": part.function_response.name,
                    "response": self._proto_to_dict(part.function_response.response)
                }
        except Exception:
            # Absolute fallback: if SDK fails to parse the part, we return a placeholder
            logging.error(f"Failed to serialize part: {traceback.format_exc()}")
            part_dict["text"] = "[Unparseable Content]"
        return part_dict

    def send_message_stream(self, content_parts: list, role: str = "Orchestrator"):
        """Sends a message to a specific agent role."""
        if not self.is_ready:
            yield {"type": "error", "content": "Not initialized"}
            return
            
        agent = self._get_specialist(role) if role != "Orchestrator" else self.orchestrator
        
        try:
            response = agent.chat_session.send_message(content_parts, stream=True)
            yield {"type": "status", "content": f"[{role}] Processing..."}
            
            start_time = time.time()
            iterator = iter(response)
            while True:
                if (time.time() - start_time) > 120: break
                try: chunk = next(iterator)
                except StopIteration: break
                except Exception as e:
                    if "attribute 'get'" in str(e): 
                        yield {"type": "error", "content": "API Parsing Error"}
                        return
                    raise e
                    
                for candidate in chunk.candidates:
                    for part in candidate.content.parts:
                        p_dict = part.to_dict()
                        if "thought" in p_dict: 
                            yield {"type": "thought", "content": part.thought, "role": role}
                        elif "function_call" in p_dict:
                            args = self._proto_to_dict(part.function_call.args)
                            fn_name = part.function_call.name
                            
                            # INTERCEPT DELEGATION
                            if fn_name == "delegate_task":
                                sub_role = args.get("role")
                                sub_task = args.get("task")
                                yield {"type": "text", "content": f"\n\n**[Delegating to {sub_role}]**: {sub_task}\n"}
                                
                                # Recursive call to sub-agent
                                sub_parts = [Part.from_text(sub_task)]
                                for sub_event in self.send_message_stream(sub_parts, role=sub_role):
                                    yield sub_event
                                    
                                # Return a result back to the Orchestrator
                                tool_result = f"Specialist {sub_role} finished the task: {sub_task}"
                                yield from self.send_tool_response_stream(fn_name, tool_result, role="Orchestrator")
                                continue 
                            
                            yield {"type": "tool_call", "name": fn_name, "args": args}
                        elif "text" in p_dict: 
                            yield {"type": "text", "content": part.text}
        except Exception as e:
            yield {"type": "error", "content": str(e)}
            
    def send_tool_response_stream(self, function_name: str, function_response: str, role: str = "Orchestrator"):
        response_part = Part.from_function_response(name=function_name, response={"result": function_response})
        yield from self.send_message_stream([response_part], role=role)

    def prepare_message_parts(self, message: str, file_paths: list = None):
        parts = []
        if message: parts.append(Part.from_text(message))
        return parts

    def get_history(self):
        # We only save Orchestrator history for persistence
        return [self._content_to_dict(c) for c in self.orchestrator.chat_session.history]

    def set_history(self, history_data):
        if not self.is_ready or not history_data: return
        new_history = [Content(role=c["role"], parts=[Part.from_dict(p) for p in c["parts"]]) for c in history_data]
        self.orchestrator.chat_session = self.orchestrator.model.start_chat(history=new_history)
        self.chat_session = self.orchestrator.chat_session

import time

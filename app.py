import customtkinter as ctk
from customtkinter import filedialog
import threading
import os
import logging
import traceback
from PIL import ImageGrab
import uuid
from agent import WebDevAgent

# Set up global logging to file for crash diagnostics
logging.basicConfig(
    filename='webdev_agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_exception(exc_type, exc_value, exc_traceback):
    """Log unhandled exceptions to file."""
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

import sys
sys.excepthook = log_exception
import json
import re

# Basic setup for CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PROJECTS_DIR = os.path.join(os.getcwd(), "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

class WebDevAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Autonomous WebDev Agent (Gemini 3.1)")
        self.geometry("1000x800")
        
        # State
        self.projects = {}
        self.current_project_id = None
        self.project_counter = 0
        self.project_buttons = []
        self.attached_files = []

        # Configure grid layout: 0 is sidebar, 1 is center chat, 2 is right action center
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Applications", font=("Arial", 20, "bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.new_btn = ctk.CTkButton(self.sidebar_frame, text="+ New App", command=self.create_new_project)
        self.new_btn.grid(row=1, column=0, padx=20, pady=(10, 5))

        self.open_btn = ctk.CTkButton(self.sidebar_frame, text="📂 Open Folder", fg_color="#4a4a4a", hover_color="#5a5a5a", command=self.open_existing_folder)
        self.open_btn.grid(row=2, column=0, padx=20, pady=(5, 10))

        self.projects_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.projects_scroll.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.sidebar_frame.grid_rowconfigure(3, weight=1)

        # --- Main Chat Area ---
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=0, column=1, sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # Chat History Text Area
        self.chat_history = ctk.CTkTextbox(self.chat_frame, state="disabled", wrap="word", font=("Consolas", 14))
        self.chat_history.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        # Attachments Display Frame
        self.attachments_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.attachments_frame.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.attachment_widgets = []
        
        # Input Frame
        self.input_frame = ctk.CTkFrame(self.chat_frame)
        self.input_frame.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        # Upload Button
        self.upload_button = ctk.CTkButton(self.input_frame, text="📎 Attach", width=60, font=("Arial", 14), command=self.attach_files)
        self.upload_button.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        # User Input Field
        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Ask the agent to build a React/Django web app with D3.js...", font=("Arial", 14))
        self.user_input.grid(row=0, column=1, padx=(5, 5), pady=10, sticky="ew")
        self.user_input.bind("<Return>", lambda event: self.send_message())
        self.user_input.bind("<Control-v>", self.handle_paste)
        
        # Send Button
        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=80, font=("Arial", 14, "bold"), command=self.send_message)
        self.send_button.grid(row=0, column=2, padx=(5, 10), pady=10)
        
        # --- Action Center (Right Panel) ---
        self.action_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.action_frame.grid(row=0, column=2, sticky="nsew", padx=(0,0))
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_rowconfigure(1, weight=1) # Log area weights
        
        self.action_title = ctk.CTkLabel(self.action_frame, text="Action Center", font=("Arial", 18, "bold"))
        self.action_title.grid(row=0, column=0, pady=10)
        
        # Live Thinking Log
        self.thinking_log = ctk.CTkTextbox(self.action_frame, state="disabled", wrap="word", font=("Consolas", 12), fg_color="#1a1a1a")
        self.thinking_log.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Approval Area (Bottom of right panel)
        self.approval_area = ctk.CTkFrame(self.action_frame, height=300, fg_color="#2b2b2b")
        self.approval_area.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.approval_area.grid_columnconfigure(0, weight=1)
        self.approval_label = ctk.CTkLabel(self.approval_area, text="No Actions Pending", font=("Arial", 14, "italic"))
        self.approval_label.pack(pady=20)
        
        # Status Bar
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.grid(row=3, column=0, columnspan=3, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready", font=("Arial", 12))
        self.status_label.pack(side="left", padx=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, orientation="horizontal", width=200, mode="indeterminate")
        self.progress_bar.pack(side="right", padx=10, pady=5)
        
        self.always_approve_cb = ctk.CTkCheckBox(self.status_frame, text="Always Approve", font=("Arial", 12), command=self._on_always_approve_toggle)
        self.always_approve_cb.pack(side="right", padx=10)
        
        # Load existing projects from disk
        self.load_all_projects()
        
        # Create a default project if none exist
        if not self.projects:
            self.create_new_project(is_initial=True)

    def create_new_project(self, is_initial=False):
        name = None
        if not is_initial:
            dialog = ctk.CTkInputDialog(text="Enter application name:", title="New Application")
            name = dialog.get_input()
            
        self.project_counter += 1
        pid = f"proj_{self.project_counter}"
        
        if not name or name.strip() == "":
            name = f"App {self.project_counter}"
        else:
            name = name.strip()
        
        # Initialize new agent session
        agent = WebDevAgent()
        initial_log = "System: Initializing WebDev Agent...\n"
        if not agent.is_ready:
            initial_log += f"System Error: {agent.init_error}\nPlease check your GCP ADC setup or API key.\n"
        else:
            initial_log += "System: Agent is ready. What would you like to build today?\n\n"
            
        self.projects[pid] = {
            "name": name,
            "agent": agent,
            "log": initial_log
        }
        
        self.save_project(pid)
        self.render_project_list()
        self.switch_project(pid)

    def open_existing_folder(self):
        folder_path = filedialog.askdirectory(title="Select Existing Development Folder")
        if not folder_path:
            return
            
        name = os.path.basename(folder_path)
        self.project_counter += 1
        pid = f"proj_{self.project_counter}"
        
        agent = WebDevAgent()
        agent.project_path = folder_path
        
        initial_log = f"System: Opened existing folder: {folder_path}\n"
        initial_log += "System: Agent is analyzing the codebase...\n\n"
        
        self.projects[pid] = {
            "name": name,
            "agent": agent,
            "log": initial_log,
            "path": folder_path
        }
        
        self.save_project(pid)
        self.render_project_list()
        self.switch_project(pid)
        
        # Guide the agent to analyze the folder
        analysis_msg = f"I have opened the folder '{folder_path}'. Please analyze the project structure and tell me what you find, then ask how you can help proceed with development."
        self.user_input.insert(0, analysis_msg)
        self.send_message()

    def save_project(self, pid):
        if pid not in self.projects: return
        data = self.projects[pid]
        save_data = {
            "name": data["name"],
            "log": data["log"],
            "path": data.get("path", os.getcwd()),
            "history": data["agent"].get_history(),
            "always_approve": self.always_approve_cb.get() if pid == self.current_project_id else data.get("always_approve", False)
        }
        file_path = os.path.join(PROJECTS_DIR, f"{pid}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save project {pid}: {e}")

    def load_all_projects(self):
        if not os.path.exists(PROJECTS_DIR): return
        
        files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith(".json")]
        for f in files:
            pid = f.replace(".json", "")
            try:
                with open(os.path.join(PROJECTS_DIR, f), "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                
                agent = WebDevAgent()
                agent.project_path = data.get("path", os.getcwd())
                agent.set_history(data.get("history", []))
                
                self.projects[pid] = {
                    "name": data["name"],
                    "agent": agent,
                    "log": data["log"],
                    "path": data.get("path"),
                    "always_approve": data.get("always_approve", False)
                }
                # Sync project counter
                try:
                    num = int(pid.split("_")[1])
                    if num > self.project_counter:
                        self.project_counter = num
                except: pass
                
            except Exception as e:
                logging.error(f"Failed to load project {f}: {e}")
        
        self.render_project_list()
        if self.projects:
            # Switch to the most recent one (last in dict)
            last_pid = list(self.projects.keys())[-1]
            self.switch_project(last_pid)

    def render_project_list(self):
        for btn in self.project_buttons:
            btn.destroy()
        self.project_buttons.clear()
        
        for pid, data in self.projects.items():
            # Highlight the currently selected project
            color = "#1f538d" if pid == self.current_project_id else "transparent"
            btn = ctk.CTkButton(self.projects_scroll, text=data["name"], fg_color=color, anchor="w",
                                command=lambda p=pid: self.switch_project(p))
            btn.pack(fill="x", pady=2)
            self.project_buttons.append(btn)

    def switch_project(self, pid):
        if not pid in self.projects:
            return
            
        # Save previous project state before switching
        if self.current_project_id and self.current_project_id != pid:
            self.save_project(self.current_project_id)
            
        self.current_project_id = pid
        self.render_project_list() # Re-render to update the highlighted button
        
        # Clear specific attachments state
        self.attached_files.clear()
        self.update_attachments_display()
        
        # Restore chat history
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.insert("end", self.projects[pid]["log"])
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")
        # Restore always approve state
        if self.projects[pid].get("always_approve"):
            self.always_approve_cb.select()
        else:
            self.always_approve_cb.deselect()

        # Clear action center on switch
        self.clear_approval_area()
        self.update_thinking_log("System: Switched to " + self.projects[pid]["name"] + "\n")

    def append_to_chat(self, text):
        if not self.winfo_exists(): return
        if not self.current_project_id: return
        try:
            self.projects[self.current_project_id]["log"] += text
            
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", text)
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")
            
            # Save progress after adding text
            self.save_project(self.current_project_id)
        except Exception:
            pass

    def handle_paste(self, event):
        """Intercept paste to check for images in the clipboard."""
        try:
            image = ImageGrab.grabclipboard()
            if image is not None:
                # If it's a list, it might be copied files
                if isinstance(image, list):
                    for file_path in image:
                        if os.path.exists(file_path):
                            self.attached_files.append(file_path)
                else:
                    # It's an actual image pixel data (e.g. Snipping Tool)
                    temp_dir = os.path.join(os.getcwd(), "temp_uploads")
                    os.makedirs(temp_dir, exist_ok=True)
                    # Generate a unique filename
                    file_name = f"clipboard_{uuid.uuid4().hex[:8]}.png"
                    file_path = os.path.join(temp_dir, file_name)
                    image.save(file_path, "PNG")
                    self.attached_files.append(file_path)
                    
                self.update_attachments_display()
                return "break"  # Stop the default paste into text box if it was an image
        except Exception as e:
            print(f"Paste error: {e}")
        
        # Let default text pasting happen otherwise
        return None
        
    def attach_files(self):
        file_paths = filedialog.askopenfilenames(title="Select Images or Files to Attach")
        if file_paths:
            self.attached_files.extend(list(file_paths))
            self.update_attachments_display()

    def remove_attachment(self, file_path):
        if file_path in self.attached_files:
            self.attached_files.remove(file_path)
            self.update_attachments_display()
            
    def update_attachments_display(self):
        # Clear existing widgets
        for widget in self.attachment_widgets:
            widget.destroy()
        self.attachment_widgets.clear()
        
        if not self.attached_files:
            return
            
        for file_path in self.attached_files:
            # Create a container frame for the item and its delete button
            item_frame = ctk.CTkFrame(self.attachments_frame, fg_color="transparent")
            item_frame.pack(side="left", padx=(0, 10))
            self.attachment_widgets.append(item_frame)
            
            try:
                from PIL import Image
                img = Image.open(file_path)
                # Create a thumbnail view
                img.thumbnail((40, 40))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                
                # Show image preview
                label = ctk.CTkLabel(item_frame, image=ctk_img, text="")
                label.pack(side="left")
            except Exception:
                # Not an image, show filename
                name = os.path.basename(file_path)
                # Truncate long names
                if len(name) > 15:
                    name = name[:12] + "..."
                label = ctk.CTkLabel(item_frame, text=f"📎 {name}", font=("Arial", 12, "italic"), text_color="gray")
                label.pack(side="left")
                
            # Add small delete button attached to this specific file_path
            # We use a default argument (fp=file_path) to bind it correctly in the lambda loop
            delete_btn = ctk.CTkButton(
                item_frame, 
                text="❌", 
                width=20, 
                height=20, 
                fg_color="transparent", 
                hover_color="#555555",
                text_color="red",
                font=("Arial", 10),
                command=lambda fp=file_path: self.remove_attachment(fp)
            )
            delete_btn.pack(side="left", padx=(2, 0), pady=(0, 20)) # Shift it up slightly

    def is_critical(self, fn_name, args):
        """Determine if a tool call requires user approval."""
        if self.always_approve_cb.get():
            return False
        
        if fn_name == "run_command":
            return True
        if fn_name == "write_file":
            path = args.get("path")
            # Overwriting an existing file is critical; creating a new one is not.
            if path and os.path.exists(path):
                return True
            return False
        # Reading, listing, and UI tools are non-critical
        return False

    def _on_always_approve_toggle(self):
        if self.current_project_id:
            self.projects[self.current_project_id]["always_approve"] = self.always_approve_cb.get()
            self.save_project(self.current_project_id)

    def rename_project_async(self, pid, user_input, agent):
        """Asynchronously generates a project name based on input and updates UI."""
        new_name = agent.generate_topic_name(user_input)
        if new_name and self.winfo_exists():
            # Apply update on UI thread
            self.after(0, lambda: self._apply_rename(pid, new_name))
            
    def _apply_rename(self, pid, new_name):
        if pid in self.projects:
            self.projects[pid]["name"] = new_name
            self.render_project_list()
            self.save_project(pid)

    def send_message(self):
        msg = self.user_input.get()
        if msg.strip() == "" and not self.attached_files:
            return
            
        # Copy current attachments and clear state
        files_to_send = list(self.attached_files)
        self.attached_files.clear()
        self.update_attachments_display()
        
        display_msg = f"You: {msg}\n"
        if files_to_send:
            display_msg += f"📎 [Attached {len(files_to_send)} file(s)]\n"
            
        self.append_to_chat(display_msg)
        self.user_input.delete(0, "end")
        
        # Disable input while processing
        self.user_input.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.upload_button.configure(state="disabled")
        
        # Check if project needs automatic renaming (if it's the first message and has default name)
        pid = self.current_project_id
        active_agent = self.projects[pid]["agent"]
        current_name = self.projects[pid]["name"]
        
        # If name is "App 1", "App 2", etc., rename based on first prompt
        if msg and re.match(r"^App \d+$", current_name):
             threading.Thread(target=self.rename_project_async, args=(pid, msg, active_agent), daemon=True).start()

        # Run agent response in a separate thread so GUI doesn't freeze
        threading.Thread(target=self.process_agent_response, args=(active_agent, msg, files_to_send), daemon=True).start()

    def process_agent_response(self, agent, msg, files_to_send, stream_generator=None, continuation_count=0):
        # Prevent infinite auto-continuation loops
        if continuation_count > 10:
            self.after(0, self.append_to_chat, "\n[System]: Maximum auto-continuation limit reached. Stopping task to prevent infinite loop.\n")
            self.after(0, self.update_status, "Stopped", False)
            self.after(0, self.re_enable_input)
            return

        self.after(0, self.update_status, "Agent is thinking...", True)
        if msg:
            self.after(0, self.update_thinking_log, f"\n--- New Turn: {msg[:50]}... ---\n")
        
        if stream_generator is None:
            try:
                # Use the agent's helper to prepare parts (handles file uploads)
                content_parts = agent.prepare_message_parts(msg, files_to_send)
                generator = agent.send_message_stream(content_parts)
            except Exception as e:
                logging.error(f"Error preparing message parts: {traceback.format_exc()}")
                self.after(0, self.append_to_chat, f"System Error: {str(e)}\n\n")
                self.after(0, self.update_status, "Error", False)
                self.after(0, self.re_enable_input)
                return
        else:
            generator = stream_generator

        try:
            for event in generator:
                etype = event.get('type')
                if etype == 'text':
                    text = event['content']
                    self.after(0, self.append_to_chat, text)
                    self.after(0, self.update_thinking_log, text)
                elif etype == 'tool_call':
                    fn_name = event['name']
                    args = event['args']
                    
                    if self.is_critical(fn_name, args):
                        # Pause and show approval UI
                        self.after(0, self.show_approval_ui, agent, fn_name, args, generator, continuation_count)
                        return 
                    else:
                        # Auto-approve and execute
                        self.after(0, self.update_thinking_log, f"\n[AUTO-APPROVED: {fn_name}]\n")
                        threading.Thread(target=self.execute_tool_and_resume, 
                                         args=(agent, fn_name, args, generator, continuation_count), 
                                         daemon=True).start()
                        return
                elif etype == 'error':
                    error_msg = event.get('content', 'Unknown Agent Error')
                    self.after(0, self.append_to_chat, f"\n[Agent Error: {error_msg}]\n")
                    self.after(0, self.update_thinking_log, f"\n[Error]: {error_msg}\n")
                    break # Stop processing on error
            
            # If we finish the entire generator without pausing for a tool, we're done with this turn.
            self.after(0, self.append_to_chat, "\n\n")
            self.after(0, self.update_thinking_log, "\n[Turn Completed]\n\n")
            self.after(0, self.update_status, "Ready", False)
            self.after(0, self.re_enable_input)
            
            # Save state after completion
            self.after(0, lambda: self.save_project(self.current_project_id))
            
        except Exception as e:
            logging.error(f"Stream Runtime Error: {traceback.format_exc()}")
            self.after(0, self.append_to_chat, f"\n[Stream Runtime Error: {str(e)}]\n\n")
            self.after(0, self.update_status, "Error", False)
            self.after(0, self.re_enable_input)

    def update_thinking_log(self, text):
        if not self.winfo_exists(): return
        try:
            self.thinking_log.configure(state="normal")
            self.thinking_log.insert("end", text)
            self.thinking_log.configure(state="disabled")
            self.thinking_log.see("end")
        except Exception:
            pass

    def update_status(self, text, busy=False):
        if not self.winfo_exists(): return
        try:
            self.status_label.configure(text=f"Status: {text}")
            if busy:
                self.progress_bar.start()
            else:
                self.progress_bar.stop()
        except Exception:
            pass

    def clear_approval_area(self):
        for widget in self.approval_area.winfo_children():
            widget.destroy()
        self.approval_label = ctk.CTkLabel(self.approval_area, text="No Actions Pending", font=("Arial", 14, "italic"))
        self.approval_label.pack(pady=20)

    def show_approval_ui(self, agent, fn_name, args, generator, continuation_count=0):
        if not self.winfo_exists(): return
        self.after(0, self.update_status, "Waiting for Approval", False)
        self.clear_approval_area()
        self.approval_label.destroy()

        label = ctk.CTkLabel(self.approval_area, text="Approval Required", font=("Arial", 16, "bold"), text_color="#3a7ebf")
        label.pack(pady=(10, 5))

        # Show Diff if write_file
        diff_text = ""
        if fn_name == "write_file":
            path = args.get("path")
            content = args.get("content")
            from tools import get_file_diff
            diff_text = get_file_diff(path, content)
            info_text = f"Action: Write File to {os.path.basename(path)}"
        else:
            info_text = f"Action: {fn_name}\nArgs: {args}"
            
        info_label = ctk.CTkLabel(self.approval_area, text=info_text, font=("Arial", 12))
        info_label.pack(pady=5)

        # Scrollable diff/details box
        details_box = ctk.CTkTextbox(self.approval_area, height=200, font=("Consolas", 11))
        details_box.pack(pady=5, padx=10, fill="both", expand=True)
        
        display_content = diff_text if diff_text else str(args)
        details_box.insert("1.0", display_content)
        details_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self.approval_area, fg_color="transparent")
        btn_frame.pack(pady=10)

        approve_btn = ctk.CTkButton(btn_frame, text="Approve", fg_color="green", hover_color="darkgreen", width=100,
                                   command=lambda: self.handle_tool_decision(agent, fn_name, args, True, generator, continuation_count))
        approve_btn.pack(side="left", padx=10)

        reject_btn = ctk.CTkButton(btn_frame, text="Reject", fg_color="red", hover_color="darkred", width=100,
                                  command=lambda: self.handle_tool_decision(agent, fn_name, args, False, generator, continuation_count))
        reject_btn.pack(side="left", padx=10)

    def handle_tool_decision(self, agent, fn_name, args, approved, generator, continuation_count=0):
        if not self.winfo_exists(): return
        self.clear_approval_area()
        
        if approved:
            self.update_thinking_log(f"\n[USER APPROVED: {fn_name}]\n")
            threading.Thread(target=self.execute_tool_and_resume, args=(agent, fn_name, args, generator, continuation_count), daemon=True).start()
        else:
            self.update_thinking_log(f"\n[USER REJECTED: {fn_name}]\n")
            # Start a fresh turn — don't pass the exhausted old generator
            rejection_parts = agent.prepare_message_parts(f"User rejected the tool call '{fn_name}'. Please suggest an alternative approach or ask the user what to do next.", [])
            rejection_generator = agent.send_message_stream(rejection_parts)
            threading.Thread(target=self.process_agent_response,
                             args=(agent, None, [], rejection_generator, continuation_count),
                             daemon=True).start()
        
        # Save state after user decision
        self.save_project(self.current_project_id)

    def execute_tool_and_resume(self, agent, fn_name, args, generator, continuation_count=0):
        self.after(0, self.update_status, "Executing Tool...", True)
        try:
            tool_fn = agent.tool_map.get(fn_name)
            if not tool_fn:
                result = f"Error: Tool {fn_name} not found."
            else:
                result = tool_fn(**args)
            
            self.after(0, self.update_thinking_log, f"[Result]: {result[:200]}...\n")
            
            # Save state after tool result is logged
            self.save_project(self.current_project_id)
            
            # Resume processing the response stream with the tool result
            threading.Thread(target=self.execute_tool_and_resume_resume, # Changed to internal helper
                             args=(agent, fn_name, result, generator, continuation_count), 
                             daemon=True).start()
        except Exception as e:
            logging.error(f"Tool Execution Error ({fn_name}): {traceback.format_exc()}")
            self.after(0, self.append_to_chat, f"\n[Execution Error: {str(e)}]\n")
            self.after(0, self.update_status, "Error", False)
            self.after(0, self.re_enable_input)
    
    def execute_tool_and_resume_resume(self, agent, fn_name, result, generator, continuation_count):
        # This is a helper to resume the response stream after the tool execution thread finishes
        self.process_agent_response_with_tool(agent, fn_name, result, generator, continuation_count)

    def process_agent_response_with_tool(self, agent, fn_name, result, generator, continuation_count=0):
        try:
            new_generator = agent.send_tool_response_stream(fn_name, result)
            
            # Track whether the model issued another tool call in this continuation
            issued_tool_call = False
            text_accumulated = ""

            for event in new_generator:
                etype = event.get('type')
                if etype == 'text':
                    text = event['content']
                    text_accumulated += text
                    self.after(0, self.append_to_chat, text)
                    self.after(0, self.update_thinking_log, text)
                elif etype == 'tool_call':
                    issued_tool_call = True
                    fn = event['name']
                    args = event['args']
                    
                    if self.is_critical(fn, args):
                        self.after(0, self.show_approval_ui, agent, fn, args, new_generator, continuation_count)
                        return
                    else:
                        self.after(0, self.update_thinking_log, f"\n[AUTO-APPROVED: {fn}]\n")
                        threading.Thread(target=self.execute_tool_and_resume, 
                                         args=(agent, fn, args, new_generator, continuation_count), 
                                         daemon=True).start()
                        return
                elif etype == 'error':
                    error_msg = event.get('content', 'Unknown Error')
                    self.after(0, self.append_to_chat, f"\n[Agent Error: {error_msg}]\n")
                    self.after(0, self.update_thinking_log, f"\n[Error]: {error_msg}\n")
                    break # Stop on error

            # If the model responded with only text and no new tool call,
            # check if the task seems complete. If not, auto-prompt to continue.
            if not issued_tool_call and text_accumulated:
                done_keywords = ["application is ready", "complete", "done", "finished", "running", "launched", "all set", "browser"]
                task_seems_done = any(kw in text_accumulated.lower() for kw in done_keywords)
                
                if not task_seems_done:
                    # Auto-continue the task
                    self.after(0, self.update_thinking_log, "\n[Auto-continuing task...]\n")
                    continuation_parts = agent.prepare_message_parts("Continue building the application. What is the next step? Keep going until it is fully complete.", [])
                    continuation_generator = agent.send_message_stream(continuation_parts)
                    self.process_agent_response(agent, None, [], continuation_generator, continuation_count + 1)
                    return

            self.after(0, self.append_to_chat, "\n\n")
            self.after(0, self.update_thinking_log, "\n[Turn Completed]\n\n")
            self.after(0, self.update_status, "Ready", False)
            self.after(0, self.re_enable_input)
            
            # Save state after completion
            self.after(0, lambda: self.save_project(self.current_project_id))

        except Exception as e:
            self.after(0, self.append_to_chat, f"\n[Tool Response Error: {str(e)}]\n")
            self.after(0, self.re_enable_input)

    def re_enable_input(self):
        if not self.winfo_exists(): return
        try:
            self.user_input.configure(state="normal", placeholder_text="Ask the agent to build a React/Django web app with D3.js...")
            self.send_button.configure(state="normal")
            self.upload_button.configure(state="normal")
            self.user_input.focus()
        except Exception:
            pass

if __name__ == "__main__":
    app = WebDevAgentApp()
    app.mainloop()

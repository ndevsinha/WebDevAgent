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
# --- Tokyo Night Theme Palette ---
PRIMARY_BG = "#1A1B26"
SIDEBAR_BG = "#16161E"
ACCENT_BLUE = "#7AA2F7"
ACCENT_PURPLE = "#BB9AF7"
TEXT_MAIN = "#C0CAF5"
TEXT_DIM = "#565F89"
SUCCESS_GREEN = "#9ECE6A"
ERROR_RED = "#F7768E"

import json
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PROJECTS_DIR = os.path.join(os.getcwd(), "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

class WebDevAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WebDev Agent Intelligence")
        self.geometry("1100x850")
        self.configure(fg_color=PRIMARY_BG)
        
        # State
        self.projects = {}
        self.current_project_id = None
        self.project_counter = 0
        self.project_buttons = []
        self.attached_files = []
        self.processing_turn = False 
        self.heartbeat_on = False

        # Configure grid layout: 0 is sidebar, 1 is center chat, 2 is right agent intelligence
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Minimalist) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PROJECTS", font=("Impact", 24), text_color=ACCENT_PURPLE)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.new_btn = ctk.CTkButton(self.sidebar_frame, text="+ Create New", font=("Arial", 13, "bold"), fg_color=ACCENT_BLUE, hover_color="#5885e6", command=self.create_new_project)
        self.new_btn.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.open_btn = ctk.CTkButton(self.sidebar_frame, text="📂 Open Workspace", font=("Arial", 12), fg_color="#24283B", hover_color="#2f354a", command=self.open_existing_folder)
        self.open_btn.grid(row=2, column=0, padx=20, pady=(5, 15), sticky="ew")

        self.projects_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent", border_width=0)
        self.projects_scroll.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
        # Bottom Dock for system buttons
        self.sidebar_dock = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_dock.grid(row=4, column=0, sticky="ew", padx=10, pady=20)
        
        self.reset_btn = ctk.CTkButton(self.sidebar_dock, text="🔄 Reset", fg_color="#414868", hover_color="#565f89", height=28, width=80, font=("Arial", 11), command=self.reset_conversation)
        self.reset_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(self.sidebar_dock, text="🛑 STOP", fg_color="#F7768E", hover_color="#c53b53", height=28, width=80, font=("Arial", 11, "bold"), state="disabled", command=self.force_stop_agent)
        self.stop_btn.pack(side="left", padx=5)

        # --- Main Workspace Area ---
        self.workspace_frame = ctk.CTkFrame(self, fg_color=PRIMARY_BG, corner_radius=0)
        self.workspace_frame.grid(row=0, column=1, sticky="nsew", padx=0)
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(1, weight=1)

        # Sticky Breadcrumb Header
        self.header_frame = ctk.CTkFrame(self.workspace_frame, height=50, fg_color="#1F2335", corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_label = ctk.CTkLabel(self.header_frame, text="Select a Project to Start", font=("Arial", 14, "bold"), text_color=ACCENT_BLUE)
        self.header_label.pack(side="left", padx=20, pady=10)
        
        self.tech_stack_label = ctk.CTkLabel(self.header_frame, text="", font=("Consolas", 11, "italic"), text_color=TEXT_DIM)
        self.tech_stack_label.pack(side="right", padx=20)

        # Chat Interface
        self.chat_history = ctk.CTkTextbox(self.workspace_frame, state="disabled", wrap="word", font=("Segoe UI", 14), fg_color=PRIMARY_BG, text_color=TEXT_MAIN, border_width=0)
        self.chat_history.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="nsew")
        
        self.attachments_frame = ctk.CTkFrame(self.workspace_frame, fg_color="transparent")
        self.attachments_frame.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.attachment_widgets = []
        
        # Modern Input Command Center
        self.input_frame = ctk.CTkFrame(self.workspace_frame, fg_color="#24283B", corner_radius=15)
        self.input_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        self.upload_button = ctk.CTkButton(self.input_frame, text="+", width=35, height=35, font=("Arial", 20), fg_color="transparent", hover_color="#2f354a", command=self.attach_files)
        # Note: we will re-bind this button in a moment if needed
        self.upload_button.grid(row=0, column=0, padx=(10, 0), pady=10)
        
        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Ask your agent to build something...", font=("Segoe UI", 14), fg_color="transparent", border_width=0, height=40)
        self.user_input.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.user_input.bind("<Return>", lambda event: self.send_message())
        self.user_input.bind("<Control-v>", self.handle_paste)
        
        self.send_button = ctk.CTkButton(self.input_frame, text="Execute", width=100, font=("Arial", 13, "bold"), fg_color=ACCENT_BLUE, command=self.send_message)
        self.send_button.grid(row=0, column=2, padx=(0, 10), pady=10)
        
        # --- Agent Intelligence (Right Panel) ---
        self.intel_frame = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=SIDEBAR_BG, border_width=1, border_color="#1F2335")
        self.intel_frame.grid(row=0, column=2, sticky="nsew")
        self.intel_frame.grid_columnconfigure(0, weight=1)
        self.intel_frame.grid_rowconfigure(1, weight=1)
        
        self.intel_title = ctk.CTkLabel(self.intel_frame, text="AGENT INTELLIGENCE", font=("Segoe UI", 13, "bold"), text_color=TEXT_DIM)
        self.intel_title.grid(row=0, column=0, pady=(25, 10))
        
        self.thinking_log = ctk.CTkTextbox(self.intel_frame, state="disabled", wrap="word", font=("Consolas", 12), fg_color="#1A1B26", text_color=TEXT_MAIN, border_width=0)
        self.thinking_log.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        
        self.approval_area = ctk.CTkFrame(self.intel_frame, height=280, fg_color="#1F2335", corner_radius=10)
        self.approval_area.grid(row=2, column=0, padx=15, pady=15, sticky="ew")
        self.approval_area.grid_columnconfigure(0, weight=1)
        self.approval_label = ctk.CTkLabel(self.approval_area, text="System Idle", font=("Arial", 13, "italic"), text_color=TEXT_DIM)
        self.approval_label.pack(pady=30)
        
        # Enhanced Status Bar
        self.status_bar = ctk.CTkFrame(self, height=35, fg_color=SIDEBAR_BG, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        self.role_badge = ctk.CTkLabel(self.status_bar, text="ORCHESTRATOR", font=("Arial", 10, "bold"), fg_color="#24283B", text_color=ACCENT_PURPLE, width=110, height=20, corner_radius=10)
        self.role_badge.pack(side="left", padx=(20, 10))
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", font=("Segoe UI", 12), text_color=TEXT_MAIN)
        self.status_label.pack(side="left")
        
        self.heartbeat_label = ctk.CTkLabel(self.status_bar, text="🟢", font=("Arial", 10))
        self.heartbeat_label.pack(side="left", padx=10)
        
        self.autonomous_mode_cb = ctk.CTkCheckBox(self.status_bar, text="Auto-Pilot", font=("Arial", 11), text_color=TEXT_DIM, border_color=TEXT_DIM, command=self._on_autonomous_mode_toggle)
        self.autonomous_mode_cb.pack(side="right", padx=15)
        
        self.always_approve_cb = ctk.CTkCheckBox(self.status_bar, text="Trust Tools", font=("Arial", 11), text_color=TEXT_DIM, border_color=TEXT_DIM, command=self._on_always_approve_toggle)
        self.always_approve_cb.pack(side="right", padx=15)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_bar, orientation="horizontal", width=120, height=4, mode="indeterminate", progress_color=ACCENT_BLUE)
        self.progress_bar.pack(side="right", padx=15)

        self.after(500, self.pulse_heartbeat)
        
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
            "log": initial_log,
            "path": agent.project_path,
            "autonomous_mode": False
        }
        
        self.save_project(pid)
        self.render_project_list()
        self.switch_project(pid)

    def open_existing_folder(self):
        folder_path = filedialog.askdirectory(title="Select Existing Development Folder")
        if not folder_path:
            return
            
        # Check if project already exists in current session
        for pid, data in self.projects.items():
            if os.path.normpath(data.get("path", "")) == os.path.normpath(folder_path):
                self.switch_project(pid)
                self.append_to_chat(f"System: Switched to existing project: {folder_path}\n")
                return

        name = os.path.basename(folder_path)
        self.project_counter += 1
        pid = f"proj_{self.project_counter}"
        
        agent = WebDevAgent(project_path=folder_path)
        
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
        analysis_msg = f"I have opened the folder '{folder_path}' as your working directory. Please start by listing the directory to understand what kind of project is this, then provide details of the structure and ask how I can help proceed."
        
        # Robustly trigger the first message without blocking
        def auto_analyze():
            self.user_input.delete(0, "end")
            self.user_input.insert(0, analysis_msg)
            self.send_message()
            
        self.after(500, auto_analyze) # Small delay to ensure UI is ready

    def save_project(self, pid):
        """Asynchronously saves the current project state to disk."""
        if pid not in self.projects: return
        
        # Take a snapshot of the UI state (must be main thread)
        p_data = self.projects[pid]
        agent = p_data["agent"]
        name = p_data["name"]
        log = p_data["log"]
        path = p_data.get("path", os.getcwd())
        always_approve = self.always_approve_cb.get() if pid == self.current_project_id else p_data.get("always_approve", False)
        autonomous_mode = self.autonomous_mode_cb.get() if pid == self.current_project_id else p_data.get("autonomous_mode", False)

        def bg_save():
            try:
                # Heavy serialization work
                history = agent.get_history()
                
                save_data = {
                    "name": name,
                    "log": log,
                    "path": path,
                    "history": history,
                    "always_approve": always_approve,
                    "autonomous_mode": autonomous_mode
                }
                # Disk I/O locked to prevent concurrent writes corrupting JSON
                if not hasattr(self, '_save_lock'):
                    self._save_lock = threading.Lock()
                    
                with self._save_lock:
                    file_path = os.path.join(PROJECTS_DIR, f"{pid}.json")
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(save_data, f, indent=2)
                
            except Exception as e:
                logging.error(f"Async Save Error for project {pid}: {e}")

        # Launch the background thread
        threading.Thread(target=bg_save, daemon=True).start()

    def force_stop_agent(self):
        """Forcefully clears the busy state and unlocks the UI."""
        self.after(0, self.update_status, "Stopped Manually", False)
        self.after(0, self.update_thinking_log, "\n[User Force-Stop]: UI Unlocked.\n")
        self.after(0, self.re_enable_input)

    def reset_conversation(self):
        """Emergency reset for the current project's conversation state."""
        if not self.current_project_id: return
        
        from tkinter import messagebox
        if not messagebox.askyesno("Reset Chat", "This will clear the current conversation history and restart the agent for this project. Your files will NOT be deleted. Proceed?"):
            return
            
        pid = self.current_project_id
        path = self.projects[pid].get("path", os.getcwd())
        
        # Re-initialize agent and clear logs
        self.projects[pid]["agent"] = WebDevAgent(project_path=path)
        self.projects[pid]["log"] = f"System: Conversation reset by user.\nProject Path: {path}\n\n"
        
        # Update UI
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.insert("end", self.projects[pid]["log"])
        self.chat_history.configure(state="disabled")
        
        self.save_project(pid)
        self.update_status("Reset Complete", False)
        self.update_thinking_log("System: Chat session reset.\n")
        self.after(0, self.re_enable_input)

    def load_all_projects(self):
        if not os.path.exists(PROJECTS_DIR): return
        
        files = [f for f in os.listdir(PROJECTS_DIR) if f.endswith(".json")]
        for f in files:
            pid = f.replace(".json", "")
            try:
                with open(os.path.join(PROJECTS_DIR, f), "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                
                agent = WebDevAgent(project_path=data.get("path", os.getcwd()))
                agent.set_history(data.get("history", []))
                
                self.projects[pid] = {
                    "name": data["name"],
                    "agent": agent,
                    "log": data["log"],
                    "path": data.get("path"),
                    "always_approve": data.get("always_approve", False),
                    "autonomous_mode": data.get("autonomous_mode", False)
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
        if not pid in self.projects: return
        self.current_project_id = pid
        self.render_project_list()
        
        # Update Header
        self.header_label.configure(text=self.projects[pid]["name"].upper())
        
        # Refresh Stack Info if log contains results
        log_content = self.projects[pid].get("log", "")
        if "Found" in log_content:
            stack_match = re.search(r"--- Found (.*?) ---", log_content)
            if stack_match:
                self.tech_stack_label.configure(text=f"STACK: {stack_match.group(1)}")
        else:
            self.tech_stack_label.configure(text="")
        
        # Clear specific attachments state
        self.attached_files.clear()
        self.update_attachments_display()
        
        # Proactive Multi-Agent Analysis: Automatically scan the project if it's the first time
        if "Project Analysis" not in self.projects[pid].get("log", ""):
            self.after(500, lambda: self.process_agent_response(self.projects[pid]["agent"], "Quickly scan this project and tell me what it is built for.", []))
        
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
            
        # Restore autonomous mode state
        if self.projects[pid].get("autonomous_mode"):
            self.autonomous_mode_cb.select()
        else:
            self.autonomous_mode_cb.deselect()

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
        
        # Multi-Agent delegation and scanning are internal/safe
        if fn_name in ["delegate_task", "project_auto_analyze"]:
            return False
            
        if fn_name == "run_command":
            return True
        if fn_name == "write_file":
            path = args.get("path")
            if path and os.path.exists(path):
                return True
            return False
        # Reading, listing, and UI tools are non-critical
        return False

    def _on_always_approve_toggle(self):
        if self.current_project_id:
            self.projects[self.current_project_id]["always_approve"] = self.always_approve_cb.get()
            self.save_project(self.current_project_id)

    def _on_autonomous_mode_toggle(self):
        if self.current_project_id:
            self.projects[self.current_project_id]["autonomous_mode"] = self.autonomous_mode_cb.get()
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
        if self.processing_turn:
            self.update_status("Agent is Busy...", True)
            return

        msg = self.user_input.get()
        if msg.strip() == "" and not self.attached_files:
            return
            
        self.processing_turn = True # Lock turn
            
        # Copy current attachments and clear state
        files_to_send = list(self.attached_files)
        self.attached_files.clear()
        self.update_attachments_display()
        
        # Atomic Busy State - Never disable the widget, just change visuals
        self.user_input.configure(placeholder_text="Agent is reasoning... please wait", text_color="gray")
        self.send_button.configure(fg_color="#333333", text="⏳", hover_color="#333333")
        self.upload_button.configure(fg_color="#333333")
        self.stop_btn.configure(state="normal", fg_color="#CD5C5C", text="🛑 STOP", hover_color="#FF0000")

        display_msg = f"You: {msg}\n"
        if files_to_send:
            display_msg += f"📎 [Attached {len(files_to_send)} file(s)]\n"
            
        self.append_to_chat(display_msg)
        
        # Check if project needs automatic renaming in a non-blocking safe way
        pid = self.current_project_id
        if pid in self.projects:
            active_agent = self.projects[pid]["agent"]
            current_name = self.projects[pid]["name"]
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

        self.after(0, self.update_status, "Agent is Thinking...", True, role="ORCHESTRATOR")
        self.after(0, self.clear_thinking_log) 
        if msg:
            self.after(0, self.update_thinking_log, f"\n--- Task Received ---\n")
        
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
                if etype == 'status':
                    # Pulsed status for heartbeats
                    self.after(0, self.update_status, event['content'], True)
                elif etype == 'thought':
                    role = event.get('role', 'ORCHESTRATOR')
                    self.after(0, self.update_thinking_log, f"[{role}]: {event['content']}\n")
                    self.after(0, self.update_status, "Reasoning...", True, role=role)
                elif etype == 'text':
                    text = event['content']
                    self.after(0, self.append_to_chat, text)
                    self.after(0, self.update_thinking_log, text)
                elif etype == 'tool_call':
                    fn_name = event['name']
                    args = event['args']
                    
                    if self.is_critical(fn_name, args):
                        # Pause and show approval UI
                        self.after(0, self.show_approval_ui, agent, fn_name, args, generator, continuation_count)
                        return # Input stays disabled while waiting for approval
                    else:
                        # Auto-approve and execute
                        self.after(0, self.update_thinking_log, f"\n[AUTO-APPROVED: {fn_name}]\n")
                        threading.Thread(target=self.execute_tool_and_resume, 
                                         args=(agent, fn_name, args, generator, continuation_count), 
                                         daemon=True).start()
                        return # Input stays disabled while tool runs
                elif etype == 'error':
                    error_msg = event.get('content', 'Unknown Agent Error')
                    self.after(0, self.append_to_chat, f"\n[Agent Error: {error_msg}]\n")
                    self.after(0, self.update_thinking_log, f"\n[Error]: {error_msg}\n")
                    break # Stop processing on error
            
            # Only reach here if the entire generator is finished without tool pausing
            self.after(0, self.append_to_chat, "\n\n")
            self.after(0, self.append_to_chat, "--- [Turn Completed] ---\n")
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

    def clear_thinking_log(self):
        if not self.winfo_exists(): return
        try:
            self.thinking_log.configure(state="normal")
            self.thinking_log.delete("1.0", "end")
            self.thinking_log.configure(state="disabled")
        except Exception:
            pass

    def update_thinking_log(self, text):
        if not self.winfo_exists(): return
        try:
            self.thinking_log.configure(state="normal")
            self.thinking_log.insert("end", text)
            self.thinking_log.configure(state="disabled")
            self.thinking_log.see("end")
        except Exception:
            pass

    def update_status(self, text, busy=False, role="ORCHESTRATOR"):
        if not self.winfo_exists(): return
        try:
            self.status_label.configure(text=text)
            self.role_badge.configure(text=role.upper())
            
            # Pulse role badge if busy
            if busy:
                self.role_badge.configure(fg_color="#3B4261")
                self.progress_bar.start()
            else:
                self.role_badge.configure(fg_color="#24283B")
                self.progress_bar.stop()
        except Exception: pass

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

        label = ctk.CTkLabel(self.approval_area, text="Permission Required", font=("Arial", 14, "bold"), text_color=ACCENT_BLUE)
        label.pack(pady=(15, 5))

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
            
        info_label = ctk.CTkLabel(self.approval_area, text=info_text, font=("Consolas", 11), text_color=TEXT_MAIN)
        info_label.pack(pady=5)

        # Scrollable diff/details box
        details_box = ctk.CTkTextbox(self.approval_area, height=180, font=("Consolas", 11), fg_color=PRIMARY_BG, text_color=TEXT_MAIN, border_width=1, border_color="#24283B")
        details_box.pack(pady=5, padx=10, fill="both", expand=True)
        
        display_content = diff_text if diff_text else str(args)
        details_box.insert("1.0", display_content)
        details_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self.approval_area, fg_color="transparent")
        btn_frame.pack(pady=10)

        approve_btn = ctk.CTkButton(btn_frame, text="Allow", font=("Arial", 12, "bold"), fg_color=ACCENT_BLUE, hover_color="#5885e6", width=100,
                                   command=lambda: self.handle_tool_decision(agent, fn_name, args, True, generator, continuation_count))
        approve_btn.pack(side="left", padx=10)

        reject_btn = ctk.CTkButton(btn_frame, text="Deny", font=("Arial", 12, "bold"), fg_color="#F7768E", hover_color="#c53b53", width=100,
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
                # Inject project path as cwd if the tool supports it
                import inspect
                sig = inspect.signature(tool_fn)
                if 'cwd' in sig.parameters:
                    args['cwd'] = agent.project_path
                
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
                if etype == 'thought':
                    self.after(0, self.update_thinking_log, f"[Reasoning]: {event['content']}\n")
                elif etype == 'text':
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
            # check if Autonomous Mode is enabled for auto-continuation.
            if not issued_tool_call and text_accumulated and self.autonomous_mode_cb.get():
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
        finally:
            self.after(0, self.re_enable_input)

    def pulse_heartbeat(self):
        """Pulsing heartbeat to keep the main event loop alive and visually active."""
        if not self.winfo_exists(): return
        self.heartbeat_on = not self.heartbeat_on
        dot = "🟢" if self.heartbeat_on else "⚪"
        try:
            self.heartbeat_label.configure(text=dot)
            # FORCE OS RE-FOCUS: Keeps the entry focused and alive in the OS event table
            if not self.processing_turn:
                self.user_input.focus_force()
            self.update() # Full Queue Flush every 500ms
        except: pass
        self.after(500, self.pulse_heartbeat)

    def re_enable_input(self):
        """Restores the visual state and unlocks the busy guard without toggling 'disabled'."""
        if not self.winfo_exists(): return
        
        self.processing_turn = False # Unlock busy guard
        
        try:
            def finish_unlock():
                if not self.winfo_exists(): return
                
                # Visual recovery (Entry was never disabled, so just restore colors)
                self.user_input.configure(placeholder_text="Ask the agent to build a React/Django web app with D3.js...", text_color=["black", "white"])
                self.send_button.configure(fg_color=["#3B8ED0", "#1F6AA5"], text="Send", hover_color=["#367E96", "#144E73"])
                self.upload_button.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                self.stop_btn.configure(state="disabled", fg_color="#333333", text="No Task", hover_color="#444444")
                
                # Re-bind for safety
                self.user_input.bind("<Return>", lambda event: self.send_message())
                
                # Final focus reclaim
                self.user_input.delete(0, "end") # Clear if leftovers exist
                self.user_input.focus_force()
                self.user_input.focus_set()
                self.user_input.focus()
                
                self.update_status("Ready", False)
                self.update() 
            
            self.after(100, finish_unlock)
            
        except Exception as e:
            logging.error(f"Error in re_enable_input: {e}")
            self.processing_turn = False

if __name__ == "__main__":
    app = WebDevAgentApp()
    app.mainloop()

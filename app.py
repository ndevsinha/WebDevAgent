import customtkinter as ctk
from customtkinter import filedialog
import threading
import os
from PIL import ImageGrab
import uuid
from agent import WebDevAgent

# Basic setup for CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
        self.new_btn.grid(row=1, column=0, padx=20, pady=10)

        self.projects_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.projects_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

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
        self.progress_bar.pack(side="right", padx=20, pady=5)
        
        # Create the first default project
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
        
        self.render_project_list()
        self.switch_project(pid)

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
        
        # Clear action center on switch
        self.clear_approval_area()
        self.update_thinking_log("System: Switched to " + self.projects[pid]["name"] + "\n")

    def append_to_chat(self, text):
        if not self.current_project_id: return
        self.projects[self.current_project_id]["log"] += text
        
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", text)
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

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
        
        # Run agent response in a separate thread so GUI doesn't freeze
        # Make sure to run it purely on the ACTIVE agent
        active_agent = self.projects[self.current_project_id]["agent"]
        threading.Thread(target=self.process_agent_response, args=(active_agent, msg, files_to_send), daemon=True).start()

    def process_agent_response(self, agent, msg, files_to_send, stream_generator=None):
        self.after(0, self.update_status, "Agent is thinking...", True)
        if msg:
            self.after(0, self.update_thinking_log, f"\n--- New Turn: {msg[:50]}... ---\n")
        
        if stream_generator is None:
            try:
                # Use the agent's helper to prepare parts (handles file uploads)
                content_parts = agent.prepare_message_parts(msg, files_to_send)
                generator = agent.send_message_stream(content_parts)
            except Exception as e:
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
                    # Pause the generator and show approval UI in Action Center
                    self.after(0, self.show_approval_ui, agent, fn_name, args, generator)
                    return # Exit this thread; handle_tool_decision will resume
                elif etype == 'error':
                    error_msg = event.get('content', 'Unknown Agent Error')
                    self.after(0, self.append_to_chat, f"\n[Agent Error: {error_msg}]\n")
                    self.after(0, self.update_thinking_log, f"\n[Error]: {error_msg}\n")
            
            # If we finish the entire generator without pausing for a tool, we're done with this turn.
            self.after(0, self.append_to_chat, "\n\n")
            self.after(0, self.update_thinking_log, "\n[Turn Completed]\n\n")
            self.after(0, self.update_status, "Ready", False)
            self.after(0, self.re_enable_input)
            
        except Exception as e:
            self.after(0, self.append_to_chat, f"\n[Stream Runtime Error: {str(e)}]\n\n")
            self.after(0, self.update_status, "Error", False)
            self.after(0, self.re_enable_input)

    def update_thinking_log(self, text):
        self.thinking_log.configure(state="normal")
        self.thinking_log.insert("end", text)
        self.thinking_log.configure(state="disabled")
        self.thinking_log.see("end")

    def update_status(self, text, busy=False):
        self.status_label.configure(text=f"Status: {text}")
        if busy:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()

    def clear_approval_area(self):
        for widget in self.approval_area.winfo_children():
            widget.destroy()
        self.approval_label = ctk.CTkLabel(self.approval_area, text="No Actions Pending", font=("Arial", 14, "italic"))
        self.approval_label.pack(pady=20)

    def show_approval_ui(self, agent, fn_name, args, generator):
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
                                   command=lambda: self.handle_tool_decision(agent, fn_name, args, True, generator))
        approve_btn.pack(side="left", padx=10)

        reject_btn = ctk.CTkButton(btn_frame, text="Reject", fg_color="red", hover_color="darkred", width=100,
                                  command=lambda: self.handle_tool_decision(agent, fn_name, args, False, generator))
        reject_btn.pack(side="left", padx=10)

    def handle_tool_decision(self, agent, fn_name, args, approved, generator):
        self.clear_approval_area()
        
        if approved:
            self.update_thinking_log(f"\n[USER APPROVED: {fn_name}]\n")
            threading.Thread(target=self.execute_tool_and_resume, args=(agent, fn_name, args, generator), daemon=True).start()
        else:
            self.update_thinking_log(f"\n[USER REJECTED: {fn_name}]\n")
            # Start a fresh turn — don't pass the exhausted old generator
            rejection_parts = agent.prepare_message_parts(f"User rejected the tool call '{fn_name}'. Please suggest an alternative approach or ask the user what to do next.", [])
            rejection_generator = agent.send_message_stream(rejection_parts)
            threading.Thread(target=self.process_agent_response,
                             args=(agent, None, [], rejection_generator),
                             daemon=True).start()

    def execute_tool_and_resume(self, agent, fn_name, args, generator):
        self.after(0, self.update_status, "Executing Tool...", True)
        try:
            tool_fn = agent.tool_map.get(fn_name)
            if not tool_fn:
                result = f"Error: Tool {fn_name} not found."
            else:
                result = tool_fn(**args)
            
            self.after(0, self.update_thinking_log, f"[Result]: {result[:200]}...\n")
            
            # Resume processing the response stream with the tool result
            threading.Thread(target=self.process_agent_response_with_tool, 
                             args=(agent, fn_name, result, generator), 
                             daemon=True).start()
        except Exception as e:
            self.after(0, self.append_to_chat, f"\n[Execution Error: {str(e)}]\n")
            self.after(0, self.update_status, "Error", False)
            self.after(0, self.re_enable_input)

    def process_agent_response_with_tool(self, agent, fn_name, result, generator):
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
                    self.after(0, self.show_approval_ui, agent, fn, args, new_generator)
                    return
                elif etype == 'error':
                    error_msg = event.get('content', 'Unknown Error')
                    self.after(0, self.append_to_chat, f"\n[Agent Error: {error_msg}]\n")
                    self.after(0, self.update_thinking_log, f"\n[Error]: {error_msg}\n")

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
                    self.process_agent_response(agent, None, [], continuation_generator)
                    return

            self.after(0, self.append_to_chat, "\n\n")
            self.after(0, self.update_thinking_log, "\n[Turn Completed]\n\n")
            self.after(0, self.update_status, "Ready", False)
            self.after(0, self.re_enable_input)

        except Exception as e:
            self.after(0, self.append_to_chat, f"\n[Tool Response Error: {str(e)}]\n")
            self.after(0, self.re_enable_input)

    def re_enable_input(self):
        self.user_input.configure(state="normal", placeholder_text="Ask the agent to build a React/Django web app with D3.js...")
        self.send_button.configure(state="normal")
        self.upload_button.configure(state="normal")
        self.user_input.focus()

if __name__ == "__main__":
    app = WebDevAgentApp()
    app.mainloop()

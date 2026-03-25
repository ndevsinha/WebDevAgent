import os
import subprocess
import difflib
import webbrowser
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn

def get_file_diff(path: str, new_content: str) -> str:
    """
    Generates a unified diff between the current file content and the new content.
    """
    try:
        if not os.path.exists(path):
            return f"--- (New File: {path}) ---\n{new_content}"
        
        with open(path, 'r', encoding='utf-8') as f:
            old_content = f.read()
            
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}"
        )
        return "".join(diff)
    except Exception as e:
        return f"Error generating diff: {str(e)}"

def run_command(command: str) -> str:
    """
    Executes a shell command and returns the output.
    Detects long-running server commands and runs them in the background to avoid hanging.
    """
    # Detect common server/blocking commands
    blocking_keywords = ["runserver", "npm start", "npm run dev", "vite", "serve", "watch"]
    is_blocking = any(kw in command.lower() for kw in blocking_keywords)

    try:
        if is_blocking:
            # Run in background using Popen
            # We don't capture output for background tasks as it would block or be lost
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=os.getcwd(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            return f"Command detected as a long-running process. Launched in background (PID: {process.pid}). The server should be starting up now."

        # Run command synchronously and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        output = result.stdout
        if result.stderr:
            output += "\n\n--- stderr ---\n\n" + result.stderr
        
        if result.returncode != 0:
            return f"Command failed with return code {result.returncode}\nOutput:\n{output}"
            
        return f"Command executed successfully.\nOutput:\n{output}"
    except Exception as e:
        return f"Failed to execute command: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at the specified path. Creates parent directories if they don't exist.
    Overwrites the file if it already exists.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Failed to write file {path}: {str(e)}"

def read_file(path: str) -> str:
    """
    Reads the content of a file at the specified path.
    """
    try:
        if not os.path.exists(path):
            return f"File not found: {path}"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file {path}: {str(e)}"

def list_directory(path: str = ".") -> str:
    """
    Lists the files and directories in the specified path.
    """
    try:
        if not os.path.exists(path):
            return f"Path not found: {path}"
        
        items = os.listdir(path)
        output_lines = [f"Contents of {os.path.abspath(path)}:"]
        for item in items:
            item_path = os.path.join(path, item)
            item_type = "(dir)" if os.path.isdir(item_path) else "(file)"
            output_lines.append(f"  {item} {item_type}")
            
        return "\n".join(output_lines)
    except Exception as e:
        return f"Failed to list directory {path}: {str(e)}"



def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return RGBColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

def create_presentation(title: str, slides: list, output_path: str) -> str:
    """
    Creates a professional PowerPoint presentation with advanced styling and flow diagram support.
    - title: Main title of the presentation.
    - slides: A list of dicts:
        {
            "title": "Slide Title",
            "content": ["points"],
            "background_color": "#RRGGBB",
            "text_color": "#RRGGBB",
            "flow_elements": [{"type": "box", "text": "Step 1", "x": 1, "y": 1}, {"type": "arrow", "from_x": 2, "from_y": 1.5}]
        }
    - output_path: .pptx save path.
    """
    try:
        prs = Presentation()
        
        # Title Slide
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = title
        slide.placeholders[1].text = "Autonomous WebDev Agent Premium Presentation"

        for s_data in slides:
            # Use blank layout for better manual control of flow diagrams if they exist
            has_flow = "flow_elements" in s_data
            layout_idx = 6 if has_flow else 1 # 6 is Blank, 1 is Title/Content
            slide = prs.slides.add_slide(prs.slide_layouts[layout_idx])
            
            # Apply Colors
            bg_hex = s_data.get("background_color", "#FFFFFF")
            txt_hex = s_data.get("text_color", "#000000")
            
            fill = slide.background.fill
            fill.solid()
            fill.fore_color.rgb = _hex_to_rgb(bg_hex)

            # Add Title if layout is blank
            if has_flow:
                title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(9), Inches(1))
                tf = title_shape.text_frame
                p = tf.paragraphs[0]
                p.text = s_data.get("title", "")
                p.font.bold = True
                p.font.size = Pt(32)
                p.font.color.rgb = _hex_to_rgb(txt_hex)
            else:
                title_place = slide.shapes.title
                title_place.text = s_data.get("title", "Untitled Slide")
                title_place.text_frame.paragraphs[0].font.color.rgb = _hex_to_rgb(txt_hex)
                
                body_place = slide.placeholders[1]
                tf = body_place.text_frame
                tf.clear()
                content = s_data.get("content", [])
                if isinstance(content, list):
                    for i, point in enumerate(content):
                        if i == 0:
                            p = tf.paragraphs[0]
                        else:
                            p = tf.add_paragraph()
                        p.text = point
                        p.font.color.rgb = _hex_to_rgb(txt_hex)
                else:
                    tf.paragraphs[0].text = str(content)
                    tf.paragraphs[0].font.color.rgb = _hex_to_rgb(txt_hex)

            # Add Flow Elements
            if has_flow:
                for elem in s_data.get("flow_elements", []):
                    etype = elem.get("type")
                    x, y = elem.get("x", 0), elem.get("y", 0)
                    w, h = elem.get("w", 2), elem.get("h", 1)
                    
                    if etype == "box":
                        # MSO_SHAPE_TYPE 1 = RECTANGLE
                        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
                        shape.text = elem.get("text", "")
                        shape.fill.solid()
                        shape.fill.fore_color.rgb = _hex_to_rgb(txt_hex)
                        shape.text_frame.paragraphs[0].font.color.rgb = _hex_to_rgb(bg_hex)
                    elif etype == "arrow":
                        fx, fy = elem.get("from_x", 0), elem.get("from_y", 0)
                        tx, ty = elem.get("to_x", 2), elem.get("to_y", 0)
                        # Use a right-arrow shape instead of a connector for reliability
                        arrow = slide.shapes.add_shape(13, Inches(fx), Inches(fy), Inches(tx - fx), Inches(0.4))
                        arrow.fill.solid()
                        arrow.fill.fore_color.rgb = _hex_to_rgb(txt_hex)

            # Add Image if provided
            image_path = s_data.get("image_path")
            if image_path and os.path.exists(image_path):
                # Put image on the right or center depending on flow
                ix = Inches(5.5) if not has_flow else Inches(1)
                iy = Inches(1.5) if not has_flow else Inches(3)
                iw = Inches(4)
                slide.shapes.add_picture(image_path, ix, iy, width=iw)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        prs.save(output_path)
        return f"Successfully created enhanced presentation at {output_path}"
    except Exception as e:
        return f"Failed to create presentation: {str(e)}"

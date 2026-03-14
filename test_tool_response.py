import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# Simple test of sending a tool response
try:
    print("Testing genai.protos.Part...")
    part = genai.protos.Part(
        function_response=genai.protos.FunctionResponse(
            name="test_tool",
            response={"result": "success"}
        )
    )
    print("genai.protos.Part created successfully:", part)
except Exception as e:
    print("Failed to create genai.protos.Part:", e)

try:
    print("Testing content_types dictionary formatting...")
    from google.generativeai.types import content_types
    # the dict way
    part_dict = {
        "function_response": {
            "name": "test_tool",
            "response": {"result": "success"}
        }
    }
    # To convert dict to content
    content = content_types.to_content([part_dict])
    print("content_types.to_content created successfully:", content)
except Exception as e:
    print("Failed to use content_types:", e)

# Test an actual mock model interaction
try:
    def test_tool():
        return "success"
        
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest", tools=[test_tool])
    chat = model.start_chat()
    # Force a tool call? Difficult.
except Exception as e:
    print("Setup error:", e)

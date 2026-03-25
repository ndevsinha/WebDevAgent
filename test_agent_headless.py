"""
Headless test: sends a math visualization request to the WebDevAgent
and prints the streamed output to verify the agent is working correctly.
"""
import sys
import os

# Make sure we are in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import WebDevAgent

def test_agent():
    print("="*60)
    print("WebDevAgent Headless Test")
    print("="*60)

    agent = WebDevAgent()

    if not agent.is_ready:
        print(f"[FAIL] Agent failed to initialize: {agent.init_error}")
        return False

    print("[OK] Agent initialized successfully.")
    print(f"     Model: {agent.model_name}")
    print()

    prompt = (
        "Create a simple math equation visualization website. "
        "Use React for the frontend and D3.js to plot equations like sin(x), x^2. "
        "Use a basic Django backend with an API endpoint that evaluates equations. "
        "Keep it simple. Start with creating the project folder structure."
    )

    print(f"Sending prompt: {prompt[:80]}...")
    print("-"*60)

    parts = agent.prepare_message_parts(prompt, [])
    
    tool_calls_made = []
    text_received = []
    errors = []

    for event in agent.send_message_stream(parts):
        etype = event.get("type")
        if etype == "text":
            chunk = event.get("content", "")
            text_received.append(chunk)
            print(chunk, end="", flush=True)
        elif etype == "tool_call":
            name = event.get("name")
            args = event.get("args", {})
            tool_calls_made.append({"name": name, "args": args})
            print(f"\n[TOOL CALL] -> {name}")
            for k, v in args.items():
                v_str = str(v)
                print(f"  {k}: {v_str[:100]}{'...' if len(v_str) > 100 else ''}")
            # Simulate executing the tool to test continuation
            tool_fn = agent.tool_map.get(name)
            if tool_fn:
                print(f"  [Executing {name}...]")
                try:
                    result = tool_fn(**args)
                    print(f"  [Result]: {str(result)[:150]}")
                    # Feed the result back and continue
                    print("-"*60)
                    print("[Resuming agent with tool result...]")
                    for cont_event in agent.send_tool_response_stream(name, str(result)):
                        ctype = cont_event.get("type")
                        if ctype == "text":
                            text_received.append(cont_event.get("content", ""))
                            print(cont_event.get("content", ""), end="", flush=True)
                        elif ctype == "tool_call":
                            tool_calls_made.append(cont_event)
                            print(f"\n[NEXT TOOL CALL] -> {cont_event.get('name')}")
                            break
                        elif ctype == "error":
                            errors.append(cont_event.get("content"))
                            print(f"\n[ERROR]: {cont_event.get('content')}")
                except Exception as e:
                    print(f"  [Tool Execution Error]: {e}")
            break
        elif etype == "error":
            err = event.get("content", "Unknown error")
            errors.append(err)
            print(f"\n[ERROR]: {err}")
            break

    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Text chunks received: {len(text_received)}")
    print(f"Tool calls made:      {len(tool_calls_made)}")
    print(f"Errors:               {len(errors)}")
    if errors:
        for e in errors:
            print(f"  - {e}")
    if tool_calls_made:
        print(f"First tool called: {tool_calls_made[0].get('name', 'N/A')}")
    
    success = len(errors) == 0 and (len(text_received) > 0 or len(tool_calls_made) > 0)
    print(f"\nResult: {'PASS' if success else 'FAIL'}")
    return success

if __name__ == "__main__":
    ok = test_agent()
    sys.exit(0 if ok else 1)

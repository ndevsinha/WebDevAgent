import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

def find_working_combo():
    load_dotenv()
    PROJECT_ID = "theta-cable-182605"
    REGIONS = ["us-central1", "us-east4", "europe-west1", "us-west1"]
    MODELS = ["gemini-1.5-flash-002", "gemini-1.5-flash", "gemini-1.5-pro-002", "gemini-1.5-pro", "gemini-1.0-pro"]
    
    for region in REGIONS:
        print(f"\n--- Testing Region: {region} ---")
        try:
            vertexai.init(project=PROJECT_ID, location=region)
            for model_id in MODELS:
                print(f"  Testing {model_id}...")
                try:
                    model = GenerativeModel(model_id)
                    # Simple prompt to test actual connectivity
                    response = model.generate_content("Hi")
                    print(f"  SUCCESS! Working Combo: Region={region}, Model={model_id}")
                    return region, model_id
                except Exception as e:
                    print(f"  Failed {model_id}: {e}")
        except Exception as e:
            print(f"  Failed to init region {region}: {e}")
    
    print("\nNo working combination found. Please check Model Garden permissions.")
    return None, None

if __name__ == "__main__":
    region, model = find_working_combo()
    if region and model:
        print(f"\nRECOMMENDED CONFIG: location='{region}', model_name='{model}'")

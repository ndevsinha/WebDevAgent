import os
from dotenv import load_dotenv
from google.cloud import aiplatform_v1

def list_model_garden():
    load_dotenv()
    PROJECT_ID = "theta-cable-182605"
    LOCATION = "us-central1"
    
    _svc_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if _svc_key:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _svc_key

    # Endpoints are usually {location}-aiplatform.googleapis.com
    client_options = {"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
    client = aiplatform_v1.ModelGardenServiceClient(client_options=client_options)
    
    parent = f"locations/{LOCATION}"
    
    print(f"Listing Model Garden resources in {parent}...")
    
    try:
        # In this client, we use list_publisher_models
        # We need to find the publisher 'google'
        request = aiplatform_v1.ListPublisherModelsRequest(
            parent=parent,
            filter='publisher="google"'
        )
        
        page_result = client.list_publisher_models(request=request)
        
        found = False
        for response in page_result:
            print(f"Found Publisher Model: {response.name}")
            found = True
        
        if not found:
            print("No publisher models found for 'google'. This usually means the project has no access to Google foundation models in this region.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_model_garden()

import os
from dotenv import load_dotenv

def check_api_enabled():
    load_dotenv()
    PROJECT_ID = "theta-cable-182605"
    
    # Manually point to the key if not set
    _svc_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if _svc_key:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _svc_key

    from google.cloud import service_usage_v1
    client = service_usage_v1.ServiceUsageClient()
    
    # The resource name of the service to check
    # Format: projects/{project}/services/{service}
    service_name = f"projects/{PROJECT_ID}/services/aiplatform.googleapis.com"
    
    # Use the Request object style
    request = service_usage_v1.GetServiceRequest(name=service_name)
    
    print(f"Checking status for: {service_name}")
    
    try:
        response = client.get_service(request=request)
        print(f"Service state: {response.state}")
        if response.state == service_usage_v1.types.State.ENABLED:
            print("Vertex AI API is ENABLED.")
        else:
            print("Vertex AI API is DISABLED.")
    except Exception as e:
        print(f"Error checking API status: {e}")

if __name__ == "__main__":
    check_api_enabled()

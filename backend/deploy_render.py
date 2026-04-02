import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY")


# -------------------------------
# Get Owner ID
# -------------------------------
def get_owner_id():

    url = "https://api.render.com/v1/owners"

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    try:
        data = response.json()
    except:
        print("❌ Failed to parse owner response")
        print(response.text)
        raise Exception("Render owner API failed")

    print("👤 Owners Response:", data)

    return data[0]["owner"]["id"]


# -------------------------------
# Detect Start Command
# -------------------------------
def detect_start_command(project_path):

    if os.path.exists(f"{project_path}/main.py"):
        return "uvicorn main:app --host 0.0.0.0 --port 10000"

    if os.path.exists(f"{project_path}/app.py"):
        return "uvicorn app:app --host 0.0.0.0 --port 10000"

    if os.path.exists(f"{project_path}/app/main.py"):
        return "uvicorn app.main:app --host 0.0.0.0 --port 10000"

    # Default fallback
    return "uvicorn main:app --host 0.0.0.0 --port 10000"


# -------------------------------
# Deploy to Render
# -------------------------------
def deploy_to_render(service_name="ai-deploy", docker_image=None):

    owner_id = get_owner_id()

    # Unique service name
    unique_name = f"{service_name}-{int(time.time())}"

    project_path = "."
    start_command = detect_start_command(project_path)

    url = "https://api.render.com/v1/services"

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "type": "web_service",
        "name": unique_name,
        "ownerId": owner_id,
        "repo": "https://github.com/render-examples/fastapi",
        "branch": "main",
        "serviceDetails": {
            "runtime": "python",
            "envSpecificDetails": {
                "buildCommand": "pip install fastapi uvicorn",
                "startCommand": start_command
            },
            "region": "oregon",
            "plan": "free"
        }
    }

    print("\n🚀 Deploy Payload:")
    print(payload)

    response = requests.post(url, headers=headers, json=payload)

    print("\n🔥 Render Response:")
    print(response.text)

    # Safe JSON handling
    try:
        response_data = response.json()
    except:
        response_data = {
            "raw_response": response.text
        }

    return {
        "status_code": response.status_code,
        "response": response_data,
        "service_name": unique_name
    }
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
# Deploy to Render
# -------------------------------
def deploy_to_render(service_name="ai-deploy", repo_url=None):

    owner_id = get_owner_id()

    unique_name = f"{service_name}-{int(time.time())}"

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
        "repo": repo_url,   # IMPORTANT FIX
        "branch": "main",
        "serviceDetails": {
            "runtime": "docker",
            "region": "oregon",
            "plan": "free"
        }
    }

    print("\n🚀 Deploy Payload:")
    print(payload)

    response = requests.post(url, headers=headers, json=payload)

    print("\n🔥 Render Response:")
    print(response.text)

    try:
        return response.json()
    except:
        return {
            "error": "Failed to parse response",
            "raw": response.text
        }
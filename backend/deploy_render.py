import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY")


def get_owner_id():

    url = "https://api.render.com/v1/owners"

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    return data[0]["owner"]["id"]


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
        "repo": repo_url,
        "branch": "main",
        "serviceDetails": {
            "runtime": "docker",
            "region": "oregon",
            "plan": "free"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        return response.json()
    except:
        return {
            "error": "Failed to parse response",
            "raw": response.text
        }
def get_service(service_id):

    url = f"https://api.render.com/v1/services/{service_id}"

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.json()
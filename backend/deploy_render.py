import requests
import time

from config import settings


def get_owner_id():

    url = "https://api.render.com/v1/owners"

    headers = {
        "Authorization": f"Bearer {settings.render_api_key}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise Exception(f"Render API error fetching owner: {response.status_code} {response.text}")

    data = response.json()

    if not data:
        raise Exception("Render API returned no owners for this API key")

    return data[0]["owner"]["id"]


def deploy_to_render(service_name="ai-deploy", repo_url=None):

    owner_id = get_owner_id()

    unique_name = f"{service_name}-{int(time.time())}"

    url = "https://api.render.com/v1/services"

    headers = {
        "Authorization": f"Bearer {settings.render_api_key}",
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
        "Authorization": f"Bearer {settings.render_api_key}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise Exception(f"Render API error fetching service: {response.status_code} {response.text}")

    return response.json()
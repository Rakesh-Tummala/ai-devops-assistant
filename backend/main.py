from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import os
import time
import subprocess
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import threading

from deploy_render import deploy_to_render, get_service

# Local Imports
from utils.zip_handler import extract_zip
from utils.project_detector import detect_project
from deployment.github_push import push_to_github

# Load environment variables
load_dotenv()

# Gemini Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

deployment_status = "Idle"
deployment_logs = []
deployment_url = None

# FastAPI app
app = FastAPI()

# Create folders
os.makedirs("generated", exist_ok=True)
os.makedirs("projects", exist_ok=True)

PORT = os.getenv("PORT", "10000")
BASE_URL = f"http://127.0.0.1:{PORT}"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------
# Models
# --------------------------------
class ChatRequest(BaseModel):
    message: str


# --------------------------------
# Extract Gemini Response
# --------------------------------
def extract_text(response):
    try:
        if response.text:
            return response.text
    except:
        pass

    try:
        return response.candidates[0].content.parts[0].text
    except:
        return "No response generated"


# --------------------------------
# Get Project Folder
# --------------------------------
def get_project_folder():
    folders = os.listdir("projects")

    for folder in folders:
        path = os.path.join("projects", folder)

        if os.path.isdir(path):
            return path

    return "projects"


# --------------------------------
# Auto Add Root Route
# --------------------------------
def add_root_route():
    project_path = get_project_folder()

    possible_files = [
        "main.py",
        "app.py",
        "app/main.py"
    ]

    for file in possible_files:
        file_path = os.path.join(project_path, file)

        if os.path.exists(file_path):

            with open(file_path, "r") as f:
                content = f.read()

            if "@app.get(\"/\")" not in content:

                route = """

@app.get("/")
def root():
    return {"message": "App Running"}
"""

                with open(file_path, "a") as f:
                    f.write(route)

                print("✅ Root route added:", file_path)
                break
deploy_status = "Idle"
logs = []
live_url = ""

@app.post("/reset-deployment/")
def reset_deployment():
    global deploy_status, logs, live_url
    deploy_status = "Idle"
    logs = []
    live_url = ""
    return {"message": "reset done"}

# --------------------------------
# Wait for Live URL
# --------------------------------
def wait_for_live_url(service_id):

    for _ in range(60):

        service_info = get_service(service_id)

        try:
            service = service_info.get("service", {})

            url = service.get("serviceDetails", {}).get("url")

            if not url:
                slug = service.get("slug")
                if slug:
                    url = f"https://{slug}.onrender.com"

            if url:
                return url

        except Exception as e:
            print("Error:", e)

        time.sleep(5)

    return None


# --------------------------------
# Deploy Logic
# --------------------------------
def deploy_render_logic():

    repo_url = "https://github.com/Rakesh-Tummala/ai-devops-assistant"

    result = deploy_to_render(
        service_name="ai-deploy-app",
        repo_url=repo_url
    )

    service_id = result.get("service", {}).get("id")

    if not service_id:
        raise Exception("Failed to create Render service")

    url = wait_for_live_url(service_id)

    return url


# --------------------------------
# CI/CD Pipeline
# --------------------------------
def run_cicd():
    global deployment_status, deployment_logs, deployment_url

    try:
        deployment_logs.clear()

        deployment_status = "Starting Deployment"
        deployment_logs.append("Starting Deployment")

        subprocess.run(
            ["git", "config", "--global", "user.email", "render@ai-devops.com"]
        )

        subprocess.run(
            ["git", "config", "--global", "user.name", "AI DevOps Bot"]
        )

        deployment_status = "Generating Dockerfile"
        deployment_logs.append("Generating Dockerfile")

        subprocess.run(
            ["curl", "-X", "POST", f"{BASE_URL}/generate-docker/"],
            check=False
        )

        deployment_status = "Pushing to GitHub"
        deployment_logs.append("Pushing to GitHub")

        push_to_github()

        deployment_status = "Deploying to Render"
        deployment_logs.append("Deploying to Render")

        deployment_logs.append("Waiting for Live URL...")

        deployment_url = deploy_render_logic()

        deployment_status = "Deployment Complete"
        deployment_logs.append("Deployment Complete")

    except Exception as e:
        deployment_status = "Error"
        deployment_logs.append(str(e))


# --------------------------------
# Upload ZIP
# --------------------------------
@app.post("/upload-zip/")
async def upload_zip(file: UploadFile = File(...)):
    file_path = f"projects/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    extract_zip(file_path)

    add_root_route()

    threading.Thread(target=run_cicd).start()

    return {"message": "ZIP uploaded and deployment started"}


# --------------------------------
# Home
# --------------------------------
@app.get("/")
def home():
    return {
        "service": "AI DevOps Deployment",
        "status": "Live",
        "docs": "/docs"
    }


# --------------------------------
# Deployment Status
# --------------------------------
@app.get("/deployment-status/")
def deployment_status_api():
    return {
        "status": deployment_status,
        "logs": deployment_logs,
        "url": deployment_url
    }


# --------------------------------
# Detect Project
# --------------------------------
@app.get("/detect-project/")
def detect():
    project_path = get_project_folder()
    project_type = detect_project(project_path)

    return {"project_type": project_type}


# --------------------------------
# Generate Dockerfile
# --------------------------------
@app.post("/generate-docker/")
async def generate_docker(
    file: UploadFile = File(None),
    project_type: str = Form(None)
):

    project_path = get_project_folder()

    if not project_type:
        project_type = detect_project(project_path)

    docker_output = ""

    if project_type in ["react", "vite", "frontend"]:

        docker_output = """
FROM node:lts-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
EXPOSE 10000
CMD ["serve", "-s", "dist", "-l", "10000"]
"""

    elif project_type in ["python", "fastapi"]:

        docker_output = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
"""

    else:

        docker_output = """
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 10000
CMD ["nginx", "-g", "daemon off;"]
"""

    filename = os.path.join(project_path, "Dockerfile")

    with open(filename, "w") as f:
        f.write(docker_output)

    return {
        "project_type": project_type,
        "saved_to": filename
    }


# --------------------------------
# Deploy API
# --------------------------------
@app.post("/deploy-render/")
def deploy_render():

    url = deploy_render_logic()

    return {
        "status": "Deploying",
        "url": url
    }


# --------------------------------
# Chat API
# --------------------------------
@app.post("/reset-deployment/")
def reset_deployment():
    global deploy_status, logs, live_url
    deploy_status = "Idle"
    logs = []
    live_url = ""
    return {"message": "Reset successful"}

@app.post("/chat/")
def chat(request: ChatRequest):

    response = model.generate_content(request.message)

    answer = extract_text(response)

    return {"response": answer}
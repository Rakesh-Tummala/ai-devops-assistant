from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import threading

from deploy_render import deploy_to_render, get_service
from utils.zip_handler import extract_zip
from utils.project_detector import detect_project
from deployment.github_push import push_to_github

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Deployment state
deployment_status = "Idle"
deployment_logs = []
deployment_url = None

app = FastAPI()

os.makedirs("generated", exist_ok=True)
os.makedirs("projects", exist_ok=True)

PORT = os.getenv("PORT", "10000")

# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------
# Models
# -----------------------
class ChatRequest(BaseModel):
    message: str


# -----------------------
# Helpers
# -----------------------
def extract_text(response):
    try:
        return response.text
    except:
        return "No response generated"


def get_project_folder():

    folders = sorted(os.listdir("projects"), reverse=True)

    for folder in folders:
        path = os.path.join("projects", folder)
        if os.path.isdir(path):
            return path

    return "projects"


# -----------------------
# Add Root Route
# -----------------------
def add_root_route():

    project_path = get_project_folder()

    possible_files = ["main.py", "app.py"]

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

                break


# -----------------------
# Reset Deployment
# -----------------------
@app.post("/reset-deployment/")
def reset_deployment():
    global deployment_status, deployment_logs, deployment_url

    deployment_status = "Idle"
    deployment_logs = []
    deployment_url = None

    return {"message": "Reset done"}


# -----------------------
# Wait for Live URL
# -----------------------
def wait_for_live_url(service_id):

    for _ in range(60):

        service = get_service(service_id)

        try:
            url = service["service"]["serviceDetails"]["url"]
            if url:
                return url
        except:
            pass

        time.sleep(5)

    return None


# -----------------------
# Deploy Logic
# -----------------------
def deploy_render_logic():

    repo_url = push_to_github()

    result = deploy_to_render(
        service_name="ai-deploy-app",
        repo_url=repo_url
    )

    if "service" not in result:
        raise Exception(f"Render Error: {result}")

    service_id = result["service"]["id"]

    url = wait_for_live_url(service_id)

    return url


# -----------------------
# CI/CD
# -----------------------
def run_cicd():

    global deployment_status, deployment_logs, deployment_url

    try:

        deployment_logs.clear()

        deployment_status = "Generating Dockerfile"
        deployment_logs.append("Generating Dockerfile")

        generate_docker()

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


# -----------------------
# Upload ZIP
# -----------------------
@app.post("/upload-zip/")
async def upload_zip(file: UploadFile = File(...)):

    file_path = f"projects/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    extract_zip(file_path)

    add_root_route()

    threading.Thread(target=run_cicd).start()

    return {"message": "Deployment started"}


# -----------------------
# Home
# -----------------------
@app.get("/")
def home():
    return {
        "service": "AI DevOps Deployment",
        "status": "Running"
    }


# -----------------------
# Status
# -----------------------
@app.get("/deployment-status/")
def deployment_status_api():
    return {
        "status": deployment_status,
        "logs": deployment_logs,
        "url": deployment_url
    }


# -----------------------
# Detect
# -----------------------
@app.get("/detect-project/")
def detect():

    project_path = get_project_folder()
    project_type = detect_project(project_path)

    return {"project_type": project_type}


# -----------------------
# Docker Generator
# -----------------------
def generate_docker():

    project_path = get_project_folder()
    project_type = detect_project(project_path)

    if project_type in ["react", "vite", "frontend"]:

        docker = """FROM node:lts-alpine
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
RUN npm install -g serve
EXPOSE 10000
CMD ["serve","-s","dist","-l","10000"]
"""

    elif os.path.exists(os.path.join(project_path, "requirements.txt")):

        docker = """FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt || true
EXPOSE 10000
CMD ["python","main.py"]
"""

    else:

        docker = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 10000
CMD ["nginx","-g","daemon off;"]
"""

    docker_path = os.path.join(project_path, "Dockerfile")

    with open(docker_path, "w") as f:
        f.write(docker)

    print("Dockerfile created at:", docker_path)

# -----------------------
# Chat
# -----------------------
@app.post("/chat/")
def chat(request: ChatRequest):

    response = model.generate_content(request.message)

    return {"response": extract_text(response)}
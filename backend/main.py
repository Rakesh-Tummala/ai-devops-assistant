from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import os
import subprocess
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
import threading
from deploy_render import deploy_to_render

# Local Imports
from utils.zip_handler import extract_zip
from utils.project_detector import detect_project
from deployment.render import deploy_render
from deployment.github_push import push_to_github

# Load environment variables
load_dotenv()

# Gemini Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
deployment_status = "Idle"
deployment_logs = []
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
# Helper function
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
# CI/CD
# --------------------------------
def run_cicd():
    global deployment_status, deployment_logs

    try:
        project_path = get_project_folder()

        deployment_status = "Generating Dockerfile"
        deployment_logs.append("Generating Dockerfile")

        subprocess.run(
            ["curl", "-X", "POST", f"{BASE_URL}/generate-docker/"],
            check=False
        )

        deployment_status = "Pushing to GitHub"
        deployment_logs.append("Pushing to GitHub")

        push_to_github(project_path)

        deployment_status = "Deploying to Render"
        deployment_logs.append("Deploying to Render")

        deploy_render()

        deployment_status = "Deployment Complete"
        deployment_logs.append("Deployment Complete")

        return "Full CI/CD completed"

    except Exception as e:
        deployment_status = "Error"
        deployment_logs.append(str(e))
        return str(e)

# --------------------------------
# Upload ZIP
# --------------------------------
@app.post("/upload-zip/")
async def upload_zip(file: UploadFile = File(...)):
    file_path = f"projects/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    extract_zip(file_path)

    threading.Thread(target=run_cicd).start()

    return {"message": "ZIP uploaded and deployment started"}


# --------------------------------
# Home
# --------------------------------
@app.get("/")
def home():
    return {"message": "AI DevOps Assistant Backend Running"}


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
@app.get("/deployment-status/")
def deployment_status_api():
    return {
        "status": deployment_status,
        "logs": deployment_logs
    }

@app.post("/generate-docker/")
async def generate_docker(
    file: UploadFile = File(None),
    project_type: str = Form(None)
):

    if file:
        file_path = f"projects/{file.filename}"

        with open(file_path, "wb") as f:
            f.write(await file.read())

        extract_zip(file_path)

    project_path = get_project_folder()

    if not project_type:
        project_type = detect_project(project_path)

    package_json_path = os.path.join(project_path, "package.json")
    start_command = 'CMD ["npm","start"]'

    if os.path.exists(package_json_path):
        import json
        with open(package_json_path) as f:
            package_data = json.load(f)

        scripts = package_data.get("scripts", {})

        if "dev" in scripts and "vite" in scripts.get("dev", ""):
            start_command = 'CMD ["npm","run","dev","--","--host"]'

        elif "start" in scripts:
            start_command = 'CMD ["npm","start"]'

        else:
            start_command = """
RUN npm run build
RUN npm install -g serve
CMD ["serve","-s","dist","-l","3000"]
"""

    response = model.generate_content(f"""
Generate a production-ready Dockerfile for a {project_type} project.

Rules:
- Use node:lts-alpine
- Set WORKDIR /app
- Copy package.json first
- Run npm install
- Copy rest of files
- Expose port 3000

Use this start command:
{start_command}

Return only Dockerfile.
""")

    docker_output = extract_text(response)

    docker_output = docker_output.replace("```dockerfile", "")
    docker_output = docker_output.replace("```", "")

    if "CMD" not in docker_output:
        docker_output += """
RUN npm run build
RUN npm install -g serve
CMD ["serve","-s","dist","-l","3000"]
"""

    filename = os.path.join(project_path, "Dockerfile")

    with open(filename, "w") as f:
        f.write(docker_output)

    return {
        "response": docker_output,
        "saved_to": filename
    }


# --------------------------------
# Build Docker
# --------------------------------
@app.post("/build-docker/")
def build_docker():
    project_path = os.path.abspath(get_project_folder())

    for root, dirs, files in os.walk(project_path):
        if "Dockerfile" in files:
            project_path = root
            break

    try:
        subprocess.run(
            ["docker", "build", "-t", "ai-devops", project_path],
            check=True
        )

        return {"message": "Docker image built successfully"}

    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# --------------------------------
# Run Docker
# --------------------------------
@app.post("/run-docker/")
def run_docker():
    try:
        subprocess.run(
            ["docker", "run", "-d", "-p", "3001:3000", "ai-devops"],
            check=True
        )

        return {"message": "Docker container running"}

    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# --------------------------------
# CI/CD Endpoint
# --------------------------------
@app.post("/cicd/")
def cicd():
    threading.Thread(target=run_cicd).start()
    return {"message": "CI/CD started"}


# --------------------------------
# Log Analyzer
# --------------------------------
@app.post("/analyze-log/")
async def analyze_log(file: UploadFile = File(...)):
    content = await file.read()

    try:
        logs = content.decode("utf-8")
    except:
        logs = content.decode("latin-1")

    response = model.generate_content(f"""
Analyze these logs and explain errors:

{logs}
""")

    analysis = extract_text(response)

    return {"analysis": analysis}


# --------------------------------
# Deploy Render
# --------------------------------
@app.post("/deploy-render/")
def deploy_render():

    service_name = "ai-deploy-app"
    docker_image = "docker.io/rakeshtummala2005/ai-devops-app:latest"

    result = deploy_to_render(service_name, docker_image)

    return result


# --------------------------------
# Chat
# --------------------------------
@app.post("/chat/")
def chat(request: ChatRequest):

    response = model.generate_content(request.message)

    answer = extract_text(response)

    return {"response": answer}
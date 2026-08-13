from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
import os
import re
import secrets
import stat
import time
from dotenv import load_dotenv
from groq import Groq, GroqError
from fastapi.middleware.cors import CORSMiddleware
import threading

from deploy_render import deploy_to_render, get_service
from utils.zip_handler import extract_zip
from utils.project_detector import detect_project
from deployment.github_push import push_to_github, scrub
import shutil
load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

APP_ACCESS_KEY = os.getenv("APP_ACCESS_KEY")
if not APP_ACCESS_KEY:
    raise RuntimeError(
        "APP_ACCESS_KEY must be set — this backend has no other access "
        "control, and every route (including the deploy flow) would "
        "otherwise be open to anyone who finds the URL."
    )


def require_access_key(x_app_key: str = Header(default="")):
    if not secrets.compare_digest(x_app_key, APP_ACCESS_KEY):
        raise HTTPException(401, "Invalid or missing access key")

# Deployment state
deployment_status = "Idle"
deployment_logs = []
deployment_url = None
deployment_lock = threading.Lock()

app = FastAPI()

os.makedirs("generated", exist_ok=True)
os.makedirs("projects", exist_ok=True)

PORT = os.getenv("PORT", "10000")

# -----------------------
# CORS
# -----------------------
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# -----------------------
# Models
# -----------------------
class ChatRequest(BaseModel):
    message: str


# -----------------------
# Upload / AI constraints
# -----------------------
SAFE_ZIP_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.zip$")
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_TEXT_INPUT_BYTES = 2 * 1024 * 1024

CICD_TARGETS = {
    "github": "a GitHub Actions workflow (intended for .github/workflows/deploy.yml)",
    "gitlab": "a GitLab CI pipeline (intended for .gitlab-ci.yml)",
    "circleci": "a CircleCI config (intended for .circleci/config.yml)",
}


# -----------------------
# Helpers
# -----------------------
def ask_groq(system_prompt, user_prompt):
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except GroqError as e:
        raise HTTPException(502, f"AI provider error: {e}")

    return completion.choices[0].message.content


async def read_capped_text(file: UploadFile, max_bytes=MAX_TEXT_INPUT_BYTES):
    raw = await file.read(max_bytes + 1)
    truncated = len(raw) > max_bytes

    if truncated:
        raw = raw[:max_bytes]

    text = raw.decode("utf-8", errors="replace")

    if truncated:
        text += "\n\n[...truncated, input exceeded the size limit...]"

    return text


def _clear_readonly_and_retry(func, path, exc_info):
    # Git marks loose object files read-only; on Windows that blocks
    # deletion outright (unlike POSIX, where only the parent dir's write
    # permission matters). Clear the flag and retry once.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def force_rmtree(path):
    shutil.rmtree(path, onerror=_clear_readonly_and_retry)


def flatten_project():
    project_path = get_project_folder()

    for item in os.listdir(project_path):
        src = os.path.join(project_path, item)
        dst = os.path.join("projects", item)

        if os.path.exists(dst):
            continue

        shutil.move(src, dst)

    # delete empty folder after moving
    if project_path != "projects":
        force_rmtree(project_path)


def get_project_folder():

    folders = sorted(os.listdir("projects"), reverse=True)

    for folder in folders:
        # Never mistake VCS/system leftovers (e.g. a stray .git from a
        # prior deploy) for the uploaded project.
        if folder.startswith("."):
            continue

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
@app.post("/reset-deployment/", dependencies=[Depends(require_access_key)])
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

    # Free-tier Docker builds on Render can take well over 5 minutes,
    # so give this more headroom than a first pass suggested.
    for _ in range(120):

        service = get_service(service_id)

        try:
            # GET /v1/services/{id} returns the service object directly —
            # unlike the list endpoint, there's no "service" wrapper key.
            url = service["serviceDetails"]["url"]
            if url:
                return url
        except (KeyError, TypeError):
            pass

        time.sleep(5)

    return None


# -----------------------
# Deploy Logic
# -----------------------
def deploy_render_logic(repo_url):

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

        repo_url = push_to_github()

        if repo_url.startswith("❌"):
            raise Exception(repo_url)

        deployment_status = "Deploying to Render"
        deployment_logs.append("Deploying to Render")

        deployment_logs.append("Waiting for Live URL...")

        deployment_url = deploy_render_logic(repo_url)

        deployment_status = "Deployment Complete"
        deployment_logs.append("Deployment Complete")

    except Exception as e:

        deployment_status = "Error"
        deployment_logs.append(scrub(str(e), os.getenv("GITHUB_TOKEN")))

    finally:

        deployment_lock.release()


# -----------------------
# Upload ZIP
# -----------------------
@app.post("/upload-zip/", dependencies=[Depends(require_access_key)])
async def upload_zip(file: UploadFile = File(...)):

    filename = os.path.basename(file.filename or "")

    if not SAFE_ZIP_NAME.match(filename):
        raise HTTPException(400, "Only a plain .zip filename is accepted")

    if not deployment_lock.acquire(blocking=False):
        raise HTTPException(409, "A deployment is already in progress")

    try:
        # Start every deployment from a clean workspace — otherwise a
        # leftover .git (or other state) from the previous deploy can be
        # mistaken for "the project folder" and corrupt this one.
        for entry in os.listdir("projects"):
            entry_path = os.path.join("projects", entry)
            if os.path.isdir(entry_path):
                force_rmtree(entry_path)
            else:
                os.remove(entry_path)

        file_path = os.path.join("projects", filename)

        size = 0
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    f.close()
                    os.remove(file_path)
                    raise HTTPException(413, "Upload too large")
                f.write(chunk)

        extract_zip(file_path)

        flatten_project()

        # Remove Git metadata files/folders
        git_items = [
            "hooks", "info", "logs", "objects",
            "refs", "config", "HEAD", "index",
            "COMMIT_EDITMSG"
        ]

        for item in git_items:
            path = os.path.join("projects", item)

            if os.path.exists(path):
                if os.path.isdir(path):
                    force_rmtree(path)
                else:
                    os.remove(path)

        add_root_route()

        threading.Thread(target=run_cicd).start()

        return {"message": "Deployment started"}

    except HTTPException:
        deployment_lock.release()
        raise

    except ValueError as e:
        deployment_lock.release()
        raise HTTPException(400, str(e))

    except Exception:
        deployment_lock.release()
        raise


# -----------------------
# Home
# -----------------------
@app.get("/")
def home():
    return {
        "service": "AI DevOps Assistant",
        "status": "Running"
    }


# -----------------------
# Status
# -----------------------
@app.get("/deployment-status/", dependencies=[Depends(require_access_key)])
def deployment_status_api():
    return {
        "status": deployment_status,
        "logs": deployment_logs,
        "url": deployment_url
    }


# -----------------------
# Detect
# -----------------------
@app.get("/detect-project/", dependencies=[Depends(require_access_key)])
def detect():

    project_path = get_project_folder()
    project_type = detect_project(project_path)

    return {"project_type": project_type}


# -----------------------
# Docker Generator (deterministic — used internally by the deploy flow)
# -----------------------
def generate_docker():

    project_path = get_project_folder()
    project_type = detect_project(project_path)
    # Move project files to root if needed
    if project_path != "projects":
        for item in os.listdir(project_path):
            src = os.path.join(project_path, item)
            dst = os.path.join("projects", item)

            if not os.path.exists(dst):
                shutil.move(src, dst)

    if project_type in ["react", "vite", "nextjs", "node", "frontend"]:

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
"""

    else:

        docker = """FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 10000
CMD ["nginx","-g","daemon off;"]
"""

    # IMPORTANT: save Dockerfile INSIDE project folder
    docker_path = os.path.join("projects", "Dockerfile")

    with open(docker_path, "w") as f:
        f.write(docker)

    return docker_path


# -----------------------
# Chat (Groq)
# -----------------------
@app.post("/chat/", dependencies=[Depends(require_access_key)])
def chat(request: ChatRequest):

    system_prompt = (
        "You are an AI DevOps assistant. Answer questions about deployment, "
        "CI/CD, containers, cloud infrastructure, and troubleshooting clearly "
        "and concisely."
    )

    reply = ask_groq(system_prompt, request.message)

    return {"response": reply}


# -----------------------
# Log Analyzer (Groq)
# -----------------------
@app.post("/analyze-log/", dependencies=[Depends(require_access_key)])
async def analyze_log(file: UploadFile = File(...)):

    log_text = await read_capped_text(file)

    system_prompt = (
        "You are a DevOps log analysis assistant. Given raw application or "
        "infrastructure logs, identify errors and their likely root causes, "
        "flag warnings worth attention, and give concrete, actionable "
        "remediation suggestions. Be specific and concise."
    )

    analysis = ask_groq(system_prompt, log_text)

    return {"analysis": analysis}


# -----------------------
# CI/CD Generator (Groq)
# -----------------------
@app.post("/generate-cicd/", dependencies=[Depends(require_access_key)])
async def generate_cicd(
    project_type: str = Form(...),
    cicd_type: str = Form("github"),
    file: Optional[UploadFile] = File(None),
):

    extra_context = ""
    if file is not None:
        extra_context = await read_capped_text(file)

    target_desc = CICD_TARGETS.get(cicd_type, f"a {cicd_type} CI/CD config")

    system_prompt = (
        "You are a DevOps engineer generating CI/CD pipeline configuration. "
        "Output ONLY the pipeline YAML/config itself — no explanation, no "
        "markdown code fences."
    )

    user_prompt = (
        f"Generate {target_desc} for a '{project_type}' project. "
        "It should install dependencies, run tests if applicable, and build "
        "the project."
    )

    if extra_context:
        user_prompt += f"\n\nAdditional project context:\n{extra_context}"

    pipeline = ask_groq(system_prompt, user_prompt)

    return {"response": pipeline}


# -----------------------
# Dockerfile Generator (Groq, standalone — separate from generate_docker() above)
# -----------------------
@app.post("/generate-docker/", dependencies=[Depends(require_access_key)])
async def generate_docker_ai(
    project_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
):

    extra_context = ""
    if file is not None:
        extra_context = await read_capped_text(file)

    system_prompt = (
        "You are a DevOps engineer writing production-ready Dockerfiles. "
        "Output ONLY the Dockerfile itself — no explanation, no markdown "
        "code fences. Prefer multi-stage builds, pinned base image versions, "
        "and a non-root user where practical."
    )

    user_prompt = f"Write a Dockerfile for a '{project_type}' project."

    if extra_context:
        user_prompt += f"\n\nProject manifest/context:\n{extra_context}"

    dockerfile = ask_groq(system_prompt, user_prompt)

    return {"response": dockerfile}

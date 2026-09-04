import os
import shutil
import stat
import time

from config import settings
from deploy_render import deploy_to_render, get_service
from deployment.github_push import push_to_github, scrub
from state import DeploymentState, deploy_dir
from utils.project_detector import detect_project

GIT_METADATA_ITEMS = [
    "hooks", "info", "logs", "objects",
    "refs", "config", "HEAD", "index",
    "COMMIT_EDITMSG",
]


def _clear_readonly_and_retry(func, path, exc_info):
    # Git marks loose object files read-only; on Windows that blocks
    # deletion outright (unlike POSIX, where only the parent dir's write
    # permission matters). Clear the flag and retry once.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def force_rmtree(path):
    shutil.rmtree(path, onerror=_clear_readonly_and_retry)


def strip_git_metadata(project_path):
    for item in GIT_METADATA_ITEMS:
        path = os.path.join(project_path, item)

        if os.path.exists(path):
            if os.path.isdir(path):
                force_rmtree(path)
            else:
                os.remove(path)


def add_root_route(project_path):
    for filename in ("main.py", "app.py"):
        file_path = os.path.join(project_path, filename)

        if not os.path.exists(file_path):
            continue

        with open(file_path, "r") as f:
            content = f.read()

        if "@app.get(\"/\")" in content:
            break

        route = """

@app.get("/")
def root():
    return {"message": "App Running"}
"""

        with open(file_path, "a") as f:
            f.write(route)

        break


def generate_docker(project_path):
    project_type = detect_project(project_path)

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

    docker_path = os.path.join(project_path, "Dockerfile")

    with open(docker_path, "w") as f:
        f.write(docker)

    return docker_path


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


def deploy_render_logic(repo_url):
    result = deploy_to_render(service_name="ai-deploy-app", repo_url=repo_url)

    if "service" not in result:
        raise Exception(f"Render Error: {result}")

    service_id = result["service"]["id"]

    return wait_for_live_url(service_id)


def prune_stale_deploy_dirs(max_age_seconds=3600):
    """A deploy directory is normally removed in run_pipeline's `finally`
    block. This only cleans up leftovers from a run that crashed hard
    enough to skip that (e.g. the process was killed mid-deploy)."""
    if not os.path.isdir("projects"):
        return

    now = time.time()

    for entry in os.listdir("projects"):
        path = os.path.join("projects", entry)

        if not os.path.isdir(path):
            continue

        try:
            age = now - os.path.getmtime(path)
        except OSError:
            continue

        if age > max_age_seconds:
            force_rmtree(path)


def run_pipeline(state: DeploymentState, deploy_id: str):
    """Runs the full deploy pipeline for one already-extracted project
    directory (projects/<deploy_id>/). Meant to run on a background
    thread; releases state.lock when done so the next upload can proceed.
    """
    project_path = deploy_dir(deploy_id)

    try:
        state.update("Generating Dockerfile", "Generating Dockerfile")
        generate_docker(project_path)

        state.update("Pushing to GitHub", "Pushing to GitHub")
        repo_url = push_to_github(project_path)

        if repo_url.startswith("❌"):
            raise Exception(repo_url)

        state.update("Deploying to Render", "Deploying to Render")
        state.logs.append("Waiting for Live URL...")

        url = deploy_render_logic(repo_url)

        state.finish(url)

    except Exception as e:
        state.fail(scrub(str(e), settings.github_token))

    finally:
        try:
            force_rmtree(project_path)
        except Exception:
            pass
        state.lock.release()

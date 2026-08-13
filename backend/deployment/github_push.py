import subprocess
import os
import base64
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_project_folder():
    folders = os.listdir("projects")

    for folder in folders:
        path = os.path.join("projects", folder)

        if os.path.isdir(path):
            return path

    return "projects"


def scrub(text, token=None):
    if not text:
        return text

    if token:
        text = text.replace(token, "***")

    # catch any leftover credentialed git URL (https://user:token@host/...)
    text = re.sub(r"https://[^/@\s]+:[^/@\s]+@", "https://***@", text)

    return text


def _run_git(args, repo_path, extra_env=None):
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        args,
        cwd=repo_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def push_to_github():
    token = None

    try:
        repo_path = "projects"

        # ✅ Get env variables properly
        username = os.getenv("GITHUB_USERNAME")
        token = os.getenv("GITHUB_TOKEN")

        if not username or not token:
            raise Exception("❌ GITHUB_USERNAME or GITHUB_TOKEN not set in .env")

        repo_name = os.getenv("GITHUB_REPO_NAME", "ai-devops-deploy")

        # No credentials embedded in the remote URL — auth is passed per-command
        # below via a git -c http.extraheader, so nothing persists into
        # projects/.git/config and nothing can leak through an echoed URL.
        repo_url = f"https://github.com/{username}/{repo_name}.git"

        basic_auth = base64.b64encode(f"{username}:{token}".encode()).decode()
        auth_header = f"http.extraheader=Authorization: Basic {basic_auth}"

        # -------------------------
        # Git init
        # -------------------------
        _run_git(["git", "init"], repo_path)

        _run_git(["git", "config", "user.email", "ai@devops.com"], repo_path)

        _run_git(["git", "config", "user.name", "AI DevOps"], repo_path)

        # -------------------------
        # Add & Commit
        # -------------------------
        _run_git(["git", "add", "."], repo_path)

        _run_git(
            ["git", "commit", "-m", "Auto deploy from AI DevOps", "--allow-empty"],
            repo_path,
        )

        # -------------------------
        # Branch
        # -------------------------
        _run_git(["git", "branch", "-M", "main"], repo_path)

        # -------------------------
        # Remote handling (safe)
        # -------------------------
        subprocess.run(
            ["git", "remote", "remove", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        _run_git(["git", "remote", "add", "origin", repo_url], repo_path)

        # -------------------------
        # Push (token passed only for this command, never persisted)
        # -------------------------
        _run_git(
            ["git", "-c", auth_header, "push", "-u", "origin", "main", "--force"],
            repo_path,
        )

        # ✅ Return CLEAN repo URL (important for Render)
        clean_url = f"https://github.com/{username}/{repo_name}"

        return clean_url

    except subprocess.CalledProcessError as e:
        detail = e.stderr or e.stdout or str(e)
        return scrub(f"❌ Git command failed: {detail}", token)

    except Exception as e:
        return scrub(f"❌ Error: {str(e)}", token)

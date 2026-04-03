import subprocess
import os
import time

def get_project_folder():
    folders = os.listdir("projects")

    for folder in folders:
        path = os.path.join("projects", folder)

        if os.path.isdir(path):
            return path

    return "projects"


def push_to_github():

    try:
        repo_path = get_project_folder()

        # Init repo
        subprocess.run(["git", "init"], cwd=repo_path, check=False)

        # Fix git config (IMPORTANT)
        subprocess.run(
            ["git", "config", "user.email", "ai@devops.com"],
            cwd=repo_path,
            check=False
        )

        subprocess.run(
            ["git", "config", "user.name", "AI DevOps"],
            cwd=repo_path,
            check=False
        )

        # Add files
        subprocess.run(["git", "add", "."], cwd=repo_path, check=False)

        # Allow empty commit (IMPORTANT FIX)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Auto deploy from AI DevOps"],
            cwd=repo_path,
            check=False
        )

        # Your repo URL
        repo_url = "https://github.com/Rakesh-Tummala/ai-devops-deploy.git"

        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=repo_path,
            check=False
        )

        # Remove existing origin
        subprocess.run(
            ["git", "remote", "remove", "origin"],
            cwd=repo_path,
            check=False
        )

        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=repo_path,
            check=False
        )

        subprocess.run(
            ["git", "push", "-u", "origin", "main", "--force"],
            cwd=repo_path,
            check=False
        )

        return repo_url

    except Exception as e:
        return str(e)
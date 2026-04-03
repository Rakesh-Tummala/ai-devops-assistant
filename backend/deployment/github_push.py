import subprocess
import os
import shutil

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

        subprocess.run(["git", "init"], cwd=repo_path)

        subprocess.run(
            ["git", "config", "user.email", "ai@devops.com"],
            cwd=repo_path
        )

        subprocess.run(
            ["git", "config", "user.name", "AI DevOps"],
            cwd=repo_path
        )

        # IMPORTANT FIX
        subprocess.run(
            ["git", "rm", "-r", "--cached", "."],
            cwd=repo_path,
            check=False
        )

        subprocess.run(["git", "add", "."], cwd=repo_path)

        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Auto deploy from AI DevOps"],
            cwd=repo_path
        )

        repo_url = "https://github.com/Rakesh-Tummala/ai-devops-deploy.git"

        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path)

        subprocess.run(
            ["git", "remote", "remove", "origin"],
            cwd=repo_path,
            check=False
        )

        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=repo_path
        )

        subprocess.run(
            ["git", "push", "-u", "origin", "main", "--force"],
            cwd=repo_path
        )

        return repo_url

    except Exception as e:
        return str(e)
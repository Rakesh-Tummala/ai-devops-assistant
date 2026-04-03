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
        project_path = get_project_folder()
        repo_path = "repo"

        # Clean repo folder
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)

        os.makedirs(repo_path, exist_ok=True)

        # Copy project to repo root
        for item in os.listdir(project_path):
            s = os.path.join(project_path, item)
            d = os.path.join(repo_path, item)

            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # Git init
        subprocess.run(["git", "init"], cwd=repo_path)

        subprocess.run(
            ["git", "config", "user.email", "ai@devops.com"],
            cwd=repo_path
        )

        subprocess.run(
            ["git", "config", "user.name", "AI DevOps"],
            cwd=repo_path
        )

        subprocess.run(["git", "add", "."], cwd=repo_path)

        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "Auto deploy from AI DevOps"],
            cwd=repo_path
        )

        repo_url = "https://github.com/Rakesh-Tummala/ai-devops-deploy.git"

        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=repo_path
        )

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
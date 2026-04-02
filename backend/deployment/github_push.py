import subprocess
import os

def push_to_github():

    try:
        repo_path = "projects"

        subprocess.run(["git", "init"], cwd=repo_path, check=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Auto deploy from AI DevOps"], cwd=repo_path, check=True)

        # Replace with your repo URL
        repo_url = "https://github.com/Rakesh-Tummala/ai-devops-deploy.git"

        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path, check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path, check=True)

        return "Pushed to GitHub successfully"

    except Exception as e:
        return str(e)
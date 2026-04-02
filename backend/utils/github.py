import subprocess
import os

def clone_repo(repo_url, folder="projects"):
    os.makedirs(folder, exist_ok=True)

    subprocess.run(["git", "clone", repo_url, folder])

    return folder
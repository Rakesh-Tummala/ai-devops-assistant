import subprocess
import os

def deploy_render():
    try:
        project_path = os.path.join(os.getcwd(), "projects")

        # Check if folder exists
        if not os.path.exists(project_path):
            return "Projects folder not found"

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_path, check=True)

        # Configure git (prevents commit error)
        subprocess.run(
            ["git", "config", "user.email", "ai@devops.com"],
            cwd=project_path,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.name", "AI DevOps"],
            cwd=project_path,
            check=True
        )

        # Add files
        subprocess.run(["git", "add", "."], cwd=project_path, check=True)

        # Commit
        subprocess.run(
            ["git", "commit", "-m", "Deploy from AI DevOps"],
            cwd=project_path,
            check=True
        )

        return "Project prepared for Render deployment"

    except Exception as e:
        return str(e)
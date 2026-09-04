import os
import json

def detect_project(project_path):

    # ---------- Node / React / Vite / Next ----------
    package_json = os.path.join(project_path, "package.json")

    if os.path.exists(package_json):
        try:
            with open(package_json) as f:
                data = json.load(f)

            deps = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }
            deps = {name.lower() for name in deps}

            if "next" in deps:
                return "nextjs"

            if "vite" in deps:
                return "vite"

            if "react" in deps:
                return "react"

            return "node"

        except:
            return "node"


    # ---------- Python Projects ----------
    requirements = os.path.join(project_path, "requirements.txt")

    if os.path.exists(requirements):
        try:
            with open(requirements) as f:
                content = f.read().lower()

            if "fastapi" in content:
                return "fastapi"

            if "flask" in content:
                return "flask"

            return "python"

        except:
            return "python"


    # ---------- FastAPI detection (main.py) ----------
    main_py = os.path.join(project_path, "main.py")

    if os.path.exists(main_py):
        with open(main_py) as f:
            content = f.read().lower()

        if "fastapi" in content:
            return "fastapi"


    # ---------- Flask detection (app.py) ----------
    app_py = os.path.join(project_path, "app.py")

    if os.path.exists(app_py):
        with open(app_py) as f:
            content = f.read().lower()

        if "flask" in content:
            return "flask"


    return "unknown"
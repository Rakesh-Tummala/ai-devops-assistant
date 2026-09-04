import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Set before any app module is imported anywhere in the test session, so
# config.Settings() never picks up whatever happens to be in the
# developer's real backend/.env.
os.environ["APP_ACCESS_KEY"] = "test-access-key"
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["GROQ_MODEL"] = "openai/gpt-oss-120b"
os.environ["GITHUB_USERNAME"] = "test-user"
os.environ["GITHUB_TOKEN"] = "test-token"
os.environ["GITHUB_REPO_NAME"] = "test-repo"
os.environ["RENDER_API_KEY"] = "test-render-key"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"

import shutil
import pytest
from fastapi.testclient import TestClient

os.chdir(BACKEND_DIR)


@pytest.fixture
def client():
    from app import app
    from state import deployment_state

    deployment_state.reset()
    with TestClient(app) as c:
        c.headers.update({"X-App-Key": "test-access-key"})
        yield c

    if os.path.isdir("projects"):
        for entry in os.listdir("projects"):
            path = os.path.join("projects", entry)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)

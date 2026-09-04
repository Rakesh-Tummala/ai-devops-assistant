"""In-memory deployment state.

This remains a single-process, single-worker assumption (documented in the
README's Known Limitations) — only one deploy pipeline runs at a time,
enforced by `lock`. What changed from the original module-level globals:
state is now a class (trivial to construct fresh instances of in tests
instead of monkeypatching module globals), and each deploy gets its own
isolated working directory under `projects/<deploy_id>/` rather than
sharing the single `projects/` folder — so a new upload can no longer
race with, or leak files into, a deploy that's still being pushed/cleaned
up, and stale directories from a crashed run are easy to identify and
prune by id.
"""
import os
import threading
import uuid
from typing import List, Optional

PROJECTS_ROOT = "projects"


class DeploymentState:
    def __init__(self):
        self.lock = threading.Lock()
        self.deploy_id: Optional[str] = None
        self.status: str = "Idle"
        self.logs: List[str] = []
        self.url: Optional[str] = None

    def start(self, deploy_id: str):
        self.deploy_id = deploy_id
        self.status = "Starting"
        self.logs = []
        self.url = None

    def update(self, status: str, log_line: Optional[str] = None):
        self.status = status
        if log_line:
            self.logs.append(log_line)

    def finish(self, url: str):
        self.status = "Deployment Complete"
        self.url = url
        self.logs.append("Deployment Complete")

    def fail(self, message: str):
        self.status = "Error"
        self.logs.append(message)

    def reset(self):
        self.deploy_id = None
        self.status = "Idle"
        self.logs = []
        self.url = None

    def snapshot(self):
        return {
            "deploy_id": self.deploy_id,
            "status": self.status,
            "logs": list(self.logs),
            "url": self.url,
        }


def new_deploy_id() -> str:
    return uuid.uuid4().hex[:12]


def deploy_dir(deploy_id: str) -> str:
    return os.path.join(PROJECTS_ROOT, deploy_id)


deployment_state = DeploymentState()

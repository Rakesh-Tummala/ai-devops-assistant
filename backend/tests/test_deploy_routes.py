import io
import os
import threading
import time
import zipfile

import routes.deploy as deploy_routes
import services.deploy_service as deploy_service


def make_zip_bytes(members: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buf.getvalue()


def wait_for_terminal_status(client, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get("/deployment-status/").json()["status"]
        if status in ("Deployment Complete", "Error"):
            return status
        time.sleep(0.05)
    raise TimeoutError("deploy pipeline did not reach a terminal status in time")


def test_upload_zip_rejects_bad_filename(client):
    resp = client.post(
        "/upload-zip/",
        files={"file": ("malware.exe", io.BytesIO(b"x"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_zip_rejects_malformed_zip(client):
    resp = client.post(
        "/upload-zip/",
        files={"file": ("proj.zip", io.BytesIO(b"not a real zip"), "application/zip")},
    )
    assert resp.status_code == 400


def test_upload_zip_happy_path(client, monkeypatch):
    monkeypatch.setattr(deploy_service, "push_to_github", lambda project_path: "https://github.com/u/r")
    monkeypatch.setattr(deploy_service, "deploy_to_render", lambda service_name, repo_url: {"service": {"id": "srv_123"}})
    monkeypatch.setattr(deploy_service, "get_service", lambda service_id: {"serviceDetails": {"url": "https://srv.onrender.com"}})

    zip_bytes = make_zip_bytes({"package.json": "{}", "src/index.js": "1"})

    resp = client.post(
        "/upload-zip/",
        files={"file": ("proj.zip", io.BytesIO(zip_bytes), "application/zip")},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "Deployment started"
    deploy_id = body["deploy_id"]
    assert deploy_id

    final_status = wait_for_terminal_status(client)
    assert final_status == "Deployment Complete"

    status = client.get("/deployment-status/").json()
    assert status["deploy_id"] == deploy_id
    assert status["url"] == "https://srv.onrender.com"

    # The per-deploy working directory is cleaned up once pushed.
    assert not os.path.isdir(os.path.join("projects", deploy_id))


def test_upload_zip_records_pipeline_failure(client, monkeypatch):
    def failing_push(project_path):
        raise Exception("git push failed")

    monkeypatch.setattr(deploy_service, "push_to_github", failing_push)

    zip_bytes = make_zip_bytes({"package.json": "{}"})
    resp = client.post(
        "/upload-zip/",
        files={"file": ("proj.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert resp.status_code == 200

    final_status = wait_for_terminal_status(client)
    assert final_status == "Error"


def test_second_upload_while_one_in_progress_is_rejected(client, monkeypatch):
    release = threading.Event()

    def slow_pipeline(state, deploy_id):
        release.wait(timeout=5)
        state.finish("https://srv.onrender.com")
        state.lock.release()

    monkeypatch.setattr(deploy_routes, "run_pipeline", slow_pipeline)

    zip_bytes = make_zip_bytes({"package.json": "{}"})

    first = client.post(
        "/upload-zip/",
        files={"file": ("proj.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert first.status_code == 200

    second = client.post(
        "/upload-zip/",
        files={"file": ("proj2.zip", io.BytesIO(zip_bytes), "application/zip")},
    )
    assert second.status_code == 409

    release.set()
    wait_for_terminal_status(client)

import io


def test_chat_returns_groq_response(client, monkeypatch):
    import routes.ai as ai_routes
    monkeypatch.setattr(ai_routes, "ask_groq", lambda system, user: "Docker is a container platform.")

    resp = client.post("/chat/", json={"message": "What is Docker?"})

    assert resp.status_code == 200
    assert resp.json() == {"response": "Docker is a container platform."}


def test_chat_surfaces_groq_errors_as_502(client, monkeypatch):
    from fastapi import HTTPException
    import routes.ai as ai_routes

    def boom(system, user):
        raise HTTPException(502, "AI provider error: model_not_found")

    monkeypatch.setattr(ai_routes, "ask_groq", boom)

    resp = client.post("/chat/", json={"message": "hi"})
    assert resp.status_code == 502


def test_analyze_log(client, monkeypatch):
    import routes.ai as ai_routes
    monkeypatch.setattr(ai_routes, "ask_groq", lambda system, user: "No errors found.")

    resp = client.post(
        "/analyze-log/",
        files={"file": ("app.log", io.BytesIO(b"INFO: all good"), "text/plain")},
    )

    assert resp.status_code == 200
    assert resp.json() == {"analysis": "No errors found."}


def test_generate_cicd(client, monkeypatch):
    import routes.ai as ai_routes
    monkeypatch.setattr(ai_routes, "ask_groq", lambda system, user: "name: CI\non: [push]")

    resp = client.post(
        "/generate-cicd/",
        data={"project_type": "node", "cicd_type": "github"},
    )

    assert resp.status_code == 200
    assert "CI" in resp.json()["response"]


def test_generate_docker(client, monkeypatch):
    import routes.ai as ai_routes
    monkeypatch.setattr(ai_routes, "ask_groq", lambda system, user: "FROM node:lts-alpine")

    resp = client.post(
        "/generate-docker/",
        data={"project_type": "node"},
    )

    assert resp.status_code == 200
    assert resp.json()["response"].startswith("FROM")

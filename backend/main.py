"""Entrypoint kept at this path/name so `uvicorn main:app` (used by the
Dockerfile, Render, and local dev) keeps working. The actual app is
assembled in app.py from the routers in routes/."""
from app import app

__all__ = ["app"]

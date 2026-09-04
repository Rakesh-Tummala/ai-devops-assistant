import secrets
from fastapi import Header, HTTPException

from config import settings


def require_access_key(x_app_key: str = Header(default="")):
    if not secrets.compare_digest(x_app_key, settings.app_access_key):
        raise HTTPException(401, "Invalid or missing access key")

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

logger = logging.getLogger("ai-devops-assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.groq_service import check_model_available
    check_model_available()
    yield


def create_app() -> FastAPI:
    warnings = settings.validate()
    for warning in warnings:
        logger.warning(warning)

    os.makedirs("projects", exist_ok=True)

    app = FastAPI(title="AI DevOps Assistant", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    from routes import ai, deploy, health

    app.include_router(health.router)
    app.include_router(deploy.router)
    app.include_router(ai.router)

    return app


app = create_app()

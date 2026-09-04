"""Pydantic request/response models for the API — gives every endpoint a
typed, documented contract instead of returning raw dicts."""
from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str


class UploadZipResponse(BaseModel):
    message: str
    deploy_id: str


class DeploymentStatusResponse(BaseModel):
    deploy_id: Optional[str] = None
    status: str
    logs: List[str]
    url: Optional[str] = None


class ResetResponse(BaseModel):
    message: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class AnalysisResponse(BaseModel):
    analysis: str


class GeneratedResponse(BaseModel):
    response: str

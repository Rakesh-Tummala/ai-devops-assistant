from fastapi import APIRouter

from models import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def home():
    return HealthResponse(service="AI DevOps Assistant", status="Running")

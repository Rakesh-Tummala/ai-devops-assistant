from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from auth import require_access_key
from models import AnalysisResponse, ChatRequest, ChatResponse, GeneratedResponse
from services.groq_service import ask_groq

router = APIRouter(dependencies=[Depends(require_access_key)])

MAX_TEXT_INPUT_BYTES = 2 * 1024 * 1024

CICD_TARGETS = {
    "github": "a GitHub Actions workflow (intended for .github/workflows/deploy.yml)",
    "gitlab": "a GitLab CI pipeline (intended for .gitlab-ci.yml)",
    "circleci": "a CircleCI config (intended for .circleci/config.yml)",
}


async def read_capped_text(file: UploadFile, max_bytes=MAX_TEXT_INPUT_BYTES) -> str:
    raw = await file.read(max_bytes + 1)
    truncated = len(raw) > max_bytes

    if truncated:
        raw = raw[:max_bytes]

    text = raw.decode("utf-8", errors="replace")

    if truncated:
        text += "\n\n[...truncated, input exceeded the size limit...]"

    return text


@router.post("/chat/", response_model=ChatResponse)
def chat(request: ChatRequest):
    system_prompt = (
        "You are an AI DevOps assistant. Answer questions about deployment, "
        "CI/CD, containers, cloud infrastructure, and troubleshooting clearly "
        "and concisely."
    )

    reply = ask_groq(system_prompt, request.message)

    return ChatResponse(response=reply)


@router.post("/analyze-log/", response_model=AnalysisResponse)
async def analyze_log(file: UploadFile = File(...)):
    log_text = await read_capped_text(file)

    system_prompt = (
        "You are a DevOps log analysis assistant. Given raw application or "
        "infrastructure logs, identify errors and their likely root causes, "
        "flag warnings worth attention, and give concrete, actionable "
        "remediation suggestions. Be specific and concise."
    )

    analysis = ask_groq(system_prompt, log_text)

    return AnalysisResponse(analysis=analysis)


@router.post("/generate-cicd/", response_model=GeneratedResponse)
async def generate_cicd(
    project_type: str = Form(...),
    cicd_type: str = Form("github"),
    file: Optional[UploadFile] = File(None),
):
    extra_context = ""
    if file is not None:
        extra_context = await read_capped_text(file)

    target_desc = CICD_TARGETS.get(cicd_type, f"a {cicd_type} CI/CD config")

    system_prompt = (
        "You are a DevOps engineer generating CI/CD pipeline configuration. "
        "Output ONLY the pipeline YAML/config itself — no explanation, no "
        "markdown code fences."
    )

    user_prompt = (
        f"Generate {target_desc} for a '{project_type}' project. "
        "It should install dependencies, run tests if applicable, and build "
        "the project."
    )

    if extra_context:
        user_prompt += f"\n\nAdditional project context:\n{extra_context}"

    pipeline = ask_groq(system_prompt, user_prompt)

    return GeneratedResponse(response=pipeline)


@router.post("/generate-docker/", response_model=GeneratedResponse)
async def generate_docker_ai(
    project_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    extra_context = ""
    if file is not None:
        extra_context = await read_capped_text(file)

    system_prompt = (
        "You are a DevOps engineer writing production-ready Dockerfiles. "
        "Output ONLY the Dockerfile itself — no explanation, no markdown "
        "code fences. Prefer multi-stage builds, pinned base image versions, "
        "and a non-root user where practical."
    )

    user_prompt = f"Write a Dockerfile for a '{project_type}' project."

    if extra_context:
        user_prompt += f"\n\nProject manifest/context:\n{extra_context}"

    dockerfile = ask_groq(system_prompt, user_prompt)

    return GeneratedResponse(response=dockerfile)

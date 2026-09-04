import os
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth import require_access_key
from models import DeploymentStatusResponse, ResetResponse, UploadZipResponse
from services.deploy_service import add_root_route, force_rmtree, prune_stale_deploy_dirs, run_pipeline, strip_git_metadata
from state import deployment_state, deploy_dir, new_deploy_id
from utils.zip_handler import extract_zip
import threading

router = APIRouter(dependencies=[Depends(require_access_key)])

SAFE_ZIP_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.zip$")
MAX_UPLOAD_BYTES = 500 * 1024 * 1024


@router.post("/upload-zip/", response_model=UploadZipResponse)
async def upload_zip(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename or "")

    if not SAFE_ZIP_NAME.match(filename):
        raise HTTPException(400, "Only a plain .zip filename is accepted")

    if not deployment_state.lock.acquire(blocking=False):
        raise HTTPException(409, "A deployment is already in progress")

    deploy_id = new_deploy_id()
    project_path = deploy_dir(deploy_id)

    try:
        prune_stale_deploy_dirs()

        os.makedirs(project_path, exist_ok=True)
        file_path = os.path.join(project_path, filename)

        size = 0
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    f.close()
                    raise HTTPException(413, "Upload too large")
                f.write(chunk)

        extract_zip(file_path, extract_to=project_path)
        os.remove(file_path)

        strip_git_metadata(project_path)
        add_root_route(project_path)

        deployment_state.start(deploy_id)
        threading.Thread(target=run_pipeline, args=(deployment_state, deploy_id)).start()

        return UploadZipResponse(message="Deployment started", deploy_id=deploy_id)

    except HTTPException:
        force_rmtree(project_path)
        deployment_state.lock.release()
        raise

    except ValueError as e:
        force_rmtree(project_path)
        deployment_state.lock.release()
        raise HTTPException(400, str(e))

    except Exception:
        force_rmtree(project_path)
        deployment_state.lock.release()
        raise


@router.get("/deployment-status/", response_model=DeploymentStatusResponse)
def deployment_status_api():
    return DeploymentStatusResponse(**deployment_state.snapshot())


@router.post("/reset-deployment/", response_model=ResetResponse)
def reset_deployment():
    deployment_state.reset()
    return ResetResponse(message="Reset done")

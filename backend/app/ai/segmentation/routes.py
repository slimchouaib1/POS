import logging
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.core.database import SessionLocal
from app.ai.segmentation.service import get_customer_segment, get_segmentation_overview, _force_reload
from app.ai.segmentation.pipeline import run_pipeline
from app.audit.models import AuditLog
from app.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/segmentation", tags=["AI - Customer Segmentation"])

# ── Concurrency guard ────────────────────────────────────────────────────
_regen_lock = threading.Lock()
_regen_status = {
    "running": False,
    "last_run": None,      # ISO timestamp
    "last_result": None,   # summary dict
}


@router.get("/customer/{customer_id}")
def customer_segment(
    customer_id: int = Path(..., gt=0),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    return get_customer_segment(customer_id)


@router.get("/overview")
def segmentation_overview(
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    data = get_segmentation_overview()
    data["last_regenerated"] = _regen_status["last_run"]
    return data


@router.get("/regenerate/status")
def regenerate_status(
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    return {
        "running": _regen_status["running"],
        "last_run": _regen_status["last_run"],
        "last_result": _regen_status["last_result"],
    }


def _run_regeneration_bg(user_id: int):
    """Background worker — runs in its own thread with its own DB session."""
    db = SessionLocal()
    try:
        result = run_pipeline(db)

        db.add(AuditLog(
            user_id=user_id,
            action="regenerate_segments",
            entity_type="segmentation",
            entity_id=None,
            details=(
                f"Segmentation regenerated: {result.get('customers_processed', 0)} customers, "
                f"{result.get('segments_produced', 0)} segments"
            ),
        ))
        db.commit()

        _regen_status["last_run"] = result["timestamp"]
        _regen_status["last_result"] = result
        logger.info("Segmentation regeneration completed successfully")

        # Force the service to reload its cached data from the fresh CSVs
        _force_reload()

    except Exception:
        logger.exception("Segmentation regeneration failed")
        _regen_status["last_result"] = {
            "status": "error",
            "message": "Segmentation regeneration failed",
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        _regen_status["running"] = False
        db.close()


@router.post("/regenerate")
def regenerate_segments(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    """Kick off a background segmentation run. Returns immediately."""
    if _regen_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="A segmentation run is already in progress. Please wait for it to finish.",
        )

    if not _regen_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Already running")

    try:
        _regen_status["running"] = True
        _regen_status["last_result"] = {"status": "running", "timestamp": datetime.utcnow().isoformat()}
        background_tasks.add_task(_run_regeneration_bg, current_user.id)
    except Exception:
        _regen_status["running"] = False
        _regen_lock.release()
        raise

    # Release lock after scheduling — the bg task sets running=False when done
    _regen_lock.release()

    return {
        "detail": "Segmentation regeneration started",
        "status": "accepted",
    }

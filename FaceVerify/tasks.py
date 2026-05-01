import logging
import shutil
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=10)
def verify_faces_task(
    self: Any,
    img1_path: str,
    img2_path: str,
    detector_backend: str,
    tmp_dir: str,
) -> dict[str, Any]:
    """Runs DeepFace.verify and always cleans up temp files."""
    try:
        from deepface import DeepFace  # deferred import — TF only loaded in worker

        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name="ArcFace",
            detector_backend=detector_backend,
            distance_metric="cosine",
            enforce_detection=True,
            align=True,
            silent=True,
        )
        return {
            "ok": True,
            "verified": bool(result.get("verified")),
            "distance": round(float(result.get("distance", 0.0)), 4),
            "threshold": round(float(result.get("threshold", 0.0)), 4),
            "confidence": round(float(result.get("confidence", 0.0)), 2),
            "model": result.get("model", "ArcFace"),
            "detector_backend": detector_backend,
            "distance_metric": result.get("distance_metric", "cosine"),
        }
    except ValueError as e:
        return {"ok": False, "error": f"No se detectó rostro: {e}"}
    except Exception as e:
        logger.exception("Error en verify_faces_task")
        return {"ok": False, "error": str(e)[:200]}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

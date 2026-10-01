"""Optional scam classifier: fine-tuned multilingual DistilBERT (spec §3.2, §5.7 step 5).

If SCAM_MODEL_DIR is blank or missing, or transformers/torch are not installed, the classifier
is disabled and `scam_probability` returns None; Fraud Shield then uses rules only.
Install with `pip install -r requirements-ml-classifier.txt`.
"""

import logging
import threading
from pathlib import Path

from app.ai.base import run_blocking
from app.core.config import settings

log = logging.getLogger(__name__)

_POSITIVE_LABELS = {"scam", "fraud", "spam", "label_1", "1"}
_pipeline = None
_pipeline_lock = threading.Lock()
_load_failed = False


def model_dir() -> Path | None:
    path = settings.resolve_path(settings.SCAM_MODEL_DIR)
    return path if path and (path / "config.json").is_file() else None


def is_available() -> bool:
    if _load_failed or model_dir() is None:
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def _load():
    global _pipeline, _load_failed
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                from transformers import pipeline

                try:
                    _pipeline = pipeline(
                        "text-classification", model=str(model_dir()), top_k=None, truncation=True, max_length=256
                    )
                except Exception:
                    _load_failed = True
                    raise
    return _pipeline


def _probability_sync(text: str) -> float:
    scores = _load()(text)
    if scores and isinstance(scores[0], list):  # batched shape
        scores = scores[0]
    for item in scores:
        if str(item["label"]).lower() in _POSITIVE_LABELS:
            return float(item["score"])
    raise ValueError(f"no scam label among {[s['label'] for s in scores]}")


async def scam_probability(text: str) -> float | None:
    """P(scam) in 0..1, or None when the classifier is unavailable or fails."""
    if not is_available():
        return None
    try:
        return await run_blocking("classifier", 1, _probability_sync, text)
    except Exception as exc:
        log.error("scam classifier failed; using rules only", extra={"error": repr(exc)})
        return None

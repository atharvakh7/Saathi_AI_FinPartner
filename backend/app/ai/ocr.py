"""OCR for Fraud Shield screenshots with Tesseract 5 (spec §5.7 step 1).

Runs `-l eng+hin+mar+tam --psm 6`. Image bytes are only held in memory; the caller discards
them right after this returns (screenshots are never stored).
"""

import io
import logging
import os
import shutil
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.ai.base import AIUnavailable, run_blocking
from app.core.config import settings

log = logging.getLogger(__name__)

OCR_LANGS = "eng+hin+mar+tam"
_MIN_WIDTH = 1000  # upscale small screenshots; Tesseract does poorly on tiny text


def _tesseract_cmd() -> str | None:
    cmd = settings.TESSERACT_CMD
    if not cmd:
        return None
    if Path(cmd).is_file():
        return cmd
    return shutil.which(cmd)


def _tessdata_dir() -> Path | None:
    path = settings.resolve_path(settings.TESSDATA_PREFIX)
    return path if path and path.is_dir() else None


def is_available() -> bool:
    if _tesseract_cmd() is None:
        return False
    tessdata = _tessdata_dir()
    if tessdata is None:
        return True  # rely on the installation's own tessdata
    return all((tessdata / f"{lang}.traineddata").is_file() for lang in OCR_LANGS.split("+"))


def _prepare(image_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img).convert("L")
    if img.width < _MIN_WIDTH:
        scale = _MIN_WIDTH / img.width
        img = img.resize((_MIN_WIDTH, round(img.height * scale)), Image.LANCZOS)
    return img


def _extract_sync(image_bytes: bytes) -> str:
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd()
    tessdata = _tessdata_dir()
    if tessdata is not None:
        os.environ["TESSDATA_PREFIX"] = str(tessdata)
    img = _prepare(image_bytes)
    try:
        return pytesseract.image_to_string(img, lang=OCR_LANGS, config="--psm 6").strip()
    finally:
        img.close()


async def extract_text(image_bytes: bytes) -> str:
    """Raises AIUnavailable if Tesseract is missing, ValueError if the bytes are not an image."""
    if not is_available():
        raise AIUnavailable("OCR is not configured")
    try:
        return await run_blocking("ocr", 2, _extract_sync, image_bytes)
    except UnidentifiedImageError as exc:
        raise ValueError("not a readable image") from exc

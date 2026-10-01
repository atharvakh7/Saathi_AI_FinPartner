"""S3-compatible object storage (MinIO locally; spec §5.11): presigned URLs and uploads."""

from functools import lru_cache

import boto3
from botocore.client import Config

from app.core.config import settings

VIDEO_URL_TTL_SEC = 60 * 60  # spec §5.11: videos 60 min
TTS_URL_TTL_SEC = 10 * 60    # spec §5.11: TTS audio 10 min


@lru_cache
def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def presigned_get(bucket: str, key: str, expires_sec: int) -> str:
    """Signing is local (no network call), so this is safe to call from async code."""
    return s3_client().generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_sec
    )


def presigned_put(bucket: str, key: str, content_type: str, expires_sec: int = 3600) -> str:
    return s3_client().generate_presigned_url(
        "put_object", Params={"Bucket": bucket, "Key": key, "ContentType": content_type}, ExpiresIn=expires_sec
    )

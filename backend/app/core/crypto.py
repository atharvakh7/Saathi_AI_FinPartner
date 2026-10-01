"""Field-level encryption (spec §8.2): Fernet with DATA_ENCRYPTION_KEY.

Used for messages.content and fraud_checks.extracted_text.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core.config import settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(settings.DATA_ENCRYPTION_KEY.encode())


def encrypt_text(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_text(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:  # wrong key or corrupted row
        raise ValueError("Could not decrypt value (check DATA_ENCRYPTION_KEY)") from exc


class EncryptedText(TypeDecorator):
    """Stores a Fernet token in a TEXT column; transparent str in Python."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else encrypt_text(value)

    def process_result_value(self, value, dialect):
        return None if value is None else decrypt_text(value)

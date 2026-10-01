"""Expo Push API client (spec §5.10): https://exp.host/--/api/v2/push/send, ≤ 100 messages per call."""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

BATCH = 100


@dataclass
class Ticket:
    ok: bool
    error: str | None = None  # e.g. "DeviceNotRegistered"


async def send(messages: list[dict]) -> list[Ticket]:
    """One ticket per message, in order. Network/HTTP failures mark the whole batch failed."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.EXPO_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {settings.EXPO_ACCESS_TOKEN}"
    tickets: list[Ticket] = []
    async with httpx.AsyncClient(timeout=20) as client:
        for i in range(0, len(messages), BATCH):
            chunk = messages[i:i + BATCH]
            try:
                resp = await client.post(settings.EXPO_PUSH_URL, json=chunk, headers=headers)
                resp.raise_for_status()
                data = resp.json().get("data") or []
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("expo push failed", extra={"error": repr(exc), "count": len(chunk)})
                tickets += [Ticket(False, "RequestFailed")] * len(chunk)
                continue
            for j in range(len(chunk)):
                t = data[j] if j < len(data) else {}
                if t.get("status") == "ok":
                    tickets.append(Ticket(True))
                else:
                    tickets.append(Ticket(False, (t.get("details") or {}).get("error") or t.get("message") or "Unknown"))
    return tickets

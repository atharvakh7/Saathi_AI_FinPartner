"""Run one background job now, without Celery (ops, demos, tests).

    .venv/Scripts/python -m app.jobs.run insights.generate_all
    .venv/Scripts/python -m app.jobs.run insights.generate_user <user_id>
    .venv/Scripts/python -m app.jobs.run --list
"""

import asyncio
import sys

from app.core.db import engine
from app.core.logging import configure_logging
from app.core.redis import redis_client
from app.jobs.registry import load_all


async def _main(name: str, args: list[str]):
    try:
        return await load_all()[name](*args)
    finally:
        await redis_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    configure_logging()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    tasks = load_all()
    if len(sys.argv) < 2 or sys.argv[1] == "--list" or sys.argv[1] not in tasks:
        print("jobs:\n  " + "\n  ".join(sorted(tasks)))
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] == "--list" else 1)
    print(asyncio.run(_main(sys.argv[1], sys.argv[2:])))

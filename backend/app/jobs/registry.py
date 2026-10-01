"""Background job registry: name -> async implementation.

Each `tasks_*.py` module registers plain async functions here. `celery_app.py` wraps every one as a
Celery task with the same name; `dispatch.py` runs them in-process when Celery is off.
"""

from collections.abc import Awaitable, Callable

TASKS: dict[str, Callable[..., Awaitable]] = {}

TASK_MODULES = (
    "app.jobs.tasks_memory",
    "app.jobs.tasks_insights",
    "app.jobs.tasks_notifications",
    "app.jobs.tasks_schemes",
    "app.jobs.tasks_maintenance",
)


def task(name: str):
    def register(fn: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        TASKS[name] = fn
        return fn

    return register


def load_all() -> dict[str, Callable[..., Awaitable]]:
    import importlib

    for module in TASK_MODULES:
        importlib.import_module(module)
    return TASKS

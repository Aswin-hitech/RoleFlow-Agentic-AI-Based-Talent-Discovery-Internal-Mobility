"""RoleFlow — Native Asynchronous Task Runner.

Executes background candidate matching and AI tasks natively using
Python's built-in threading and ThreadPoolExecutor without external Redis/Celery daemons.
"""

import logging
import threading
import uuid
from typing import Any, Callable

logger = logging.getLogger(__name__)


def dispatch_async(fn: Callable, *args: Any, **kwargs: Any) -> threading.Thread:
    """Dispatch a background task cleanly in a daemon thread."""
    thread = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


# Backward compatibility shim for legacy task wrappers
class NativeTask:
    def __init__(self, fn: Callable):
        self.fn = fn
        self.id = "native-task"

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> "NativeTask":
        self.id = f"task-{uuid.uuid4().hex[:8]}"
        dispatch_async(self.fn, *args, **kwargs)
        return self


class NativeTaskManager:
    def task(self, *args: Any, **kwargs: Any) -> Callable:
        def decorator(fn: Callable) -> NativeTask:
            return NativeTask(fn)
        return decorator


celery_app = NativeTaskManager()

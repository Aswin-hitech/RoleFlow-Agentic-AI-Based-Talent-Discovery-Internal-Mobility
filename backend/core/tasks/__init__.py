import logging
from ..config import Config

logger = logging.getLogger(__name__)

try:
    from celery import Celery

    celery_app = Celery(
        "roleflow",
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=["core.tasks.discovery"],
    )

    celery_app.conf.update(
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        broker_connection_retry=False,
        broker_connection_max_retries=1,
        broker_transport_options={"connect_timeout": 3},
        result_backend_transport_options={"socket_connect_timeout": 3},
    )
except ImportError:
    logger.info("Celery not installed; using local asynchronous task shim")

    class DummyTask:
        def __init__(self, fn):
            self.fn = fn
            self.id = "local-task-01"

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def delay(self, *args, **kwargs):
            import threading
            import uuid
            self.id = f"task-{uuid.uuid4().hex[:8]}"
            t = threading.Thread(target=self.fn, args=args, kwargs=kwargs, daemon=True)
            t.start()
            return self

    class DummyCelery:
        def __init__(self):
            self.conf = type("Conf", (), {"broker_url": Config.CELERY_BROKER_URL})()

        def task(self, *args, **kwargs):
            def decorator(fn):
                return DummyTask(fn)
            return decorator

    celery_app = DummyCelery()

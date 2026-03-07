import logging

from django.conf import settings


logger = logging.getLogger(__name__)


def enqueue_task_or_run(task_func, *args, **kwargs):
    """
    Try to enqueue a Celery task and fall back to synchronous execution when
    the broker is unavailable or Celery is not configured.
    """
    delay = getattr(task_func, "delay", None)
    if delay is None:
        return task_func(*args, **kwargs)

    try:
        return delay(*args, **kwargs)
    except Exception as exc:  # pragma: no cover - backend-specific failures
        if not getattr(settings, "CELERY_TASK_SYNC_FALLBACK", True):
            raise
        logger.warning(
            "Celery broker unavailable for %s, running synchronously instead: %s",
            getattr(task_func, "__name__", str(task_func)),
            exc,
        )
        return task_func(*args, **kwargs)

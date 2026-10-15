import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "security.log"

security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)
security_logger.propagate = False

if not security_logger.handlers:
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


def log_security_event(event: str, user_id: int | None = None,
                       detail: str = "") -> None:
    """Write a security event without logging passwords or tokens."""
    safe_detail = str(detail).replace("\r", " ").replace("\n", " ")
    security_logger.info(
        "event=%s | user_id=%s | detail=%s",
        event,
        user_id if user_id is not None else "unknown",
        safe_detail[:300],
    )

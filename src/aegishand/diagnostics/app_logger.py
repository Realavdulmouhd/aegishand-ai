from __future__ import annotations

import logging
from pathlib import Path


def build_logger(name: str, level: str = "INFO", file_path: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(_parse_level(level))
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if file_path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _parse_level(level: str) -> int:
    normalized = level.strip().upper()
    return getattr(logging, normalized, logging.INFO)
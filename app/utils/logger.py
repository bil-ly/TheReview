import logging
import logging.config
import os
from datetime import datetime


def get_logging_config(
    name: str = __name__,
    level: int | str = logging.DEBUG,
    log_to_std_out: bool = False,
    multithreaded: bool = False,
) -> dict:
    """
    Generates a logging configuration dictionary.
    """
    if multithreaded:
        formatter_format = "%(asctime)s - %(name)s - %(filename)s - %(module)s - %(process)d - %(taskName)s - %(threadName)s - %(thread)d - %(levelname)s - %(message)s"
    else:
        formatter_format = (
            "%(asctime)s - %(name)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s"
        )

    formatters = {"custom": {"format": formatter_format}}
    handlers = {}
    if log_to_std_out:
        handlers["console"] = {
            "class": "rich.logging.RichHandler",
            "level": level,
            "formatter": "custom",
            "rich_tracebacks": True,
        }

    # Only add file handler if not in stdout-only mode or if logs directory is writable
    try:
        log_file = f"logs/{name}/{datetime.now().strftime('%y_%m_%d')}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "custom",
            "filename": log_file,
            "mode": "a",
        }
    except (PermissionError, OSError):
        # Skip file logging if we can't create the directory
        pass

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            name: {"level": level, "handlers": handlers, "propagate": False},
        },
    }
    return logging_config


def get_logger(
    name: str = __name__,
    level: int | str = logging.DEBUG,
    log_to_std_out: bool = False,
    multithreaded: bool = False,
) -> logging.Logger:
    config = get_logging_config(
        name=name,
        level=level,
        log_to_std_out=log_to_std_out,
        multithreaded=multithreaded,
    )
    logging.config.dictConfig(config)
    return logging.getLogger(name)

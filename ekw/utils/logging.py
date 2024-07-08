import os
from logging.config import dictConfig


def setup_logging() -> None:
    from .settings import Settings
    os.environ['WDM_LOG_LEVEL'] = '0'

    cfg = Settings.load()

    return dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "[%(levelname)s] [%(name)s] %(asctime)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "filename": cfg.log_file.absolute(),
                    "mode": "w",
                },
            },
            "loggers": {
                "": {"level": "DEBUG", "handlers": ["console", "file"]},
                "selenium": {"disabled": True, "propagate": False, "level": "CRITICAL"},
                "urllib3": {"disabled": True, "propagate": False, "level": "CRITICAL"},
            },
        }
    )

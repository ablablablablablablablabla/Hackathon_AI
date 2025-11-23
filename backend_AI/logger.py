import logging
import sys
import json
from pythonjsonlogger import jsonlogger


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("scientific_analyzer")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            rename_fields={"levelname": "severity", "name": "logger"}
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()
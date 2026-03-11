import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)

def get_logger(name="dvd_slackbot"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_request(logger, user, question, tables_used=None, generated_code=None, guardrail_triggers=None, result_shape=None, latency_ms=None):
    extra = {
        "user": user,
        "question": question,
        "tables_used": tables_used or [],
        "generated_code": generated_code,
        "guardrail_triggers": guardrail_triggers or [],
        "result_shape": result_shape,
        "latency_ms": latency_ms
    }
    logger.info("Request processed", extra={"extra_data": extra})
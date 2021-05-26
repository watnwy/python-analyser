import logging
from contextvars import ContextVar
from uuid import UUID, uuid4

context_logger: ContextVar[logging.Logger] = ContextVar("logger")
analyser_id: ContextVar[UUID] = ContextVar("analyser_run_id")


class PrivateEndpointsFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().find("/_/") == -1


class AnalyserFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        record.__dict__.update({"analyser_id": analyser_id.get()})
        return True


def register_analysis_logger(f):
    analyser_id.set(uuid4())
    logger = logging.getLogger(f"watnwy.analysis.{f.__module__}.{f.__name__}")
    logger.addFilter(AnalyserFilter())
    context_logger.set(logger)


def analysis_logger():
    return context_logger.get()

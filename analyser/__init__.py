import asyncio
import logging
from functools import wraps
from typing import List

from analyser import models
from analyser.logging_ import analysis_logger, register_analysis_logger

logger = logging.getLogger("watnwy")

_analyses = []


def analysis(f):
    @wraps(f)
    async def wrapper(
        project_path: str,
    ) -> List[models.AnalysisObject]:
        register_analysis_logger(f)
        analysis_logger().debug(f"analysis {f.__module__}:{f.__name__} starts")
        ret = await f(project_path)
        analysis_logger().debug(f"analysis {f.__module__}:{f.__name__} ends")
        return ret

    _analyses.append(wrapper)
    logger.debug(f"registering analysis {f.__module__}:{f.__name__}")

    return wrapper


async def run_analyses(project_path: str):
    return [
        obj
        for objects in await asyncio.gather(
            *(run_analysis(project_path) for run_analysis in _analyses)
        )
        for obj in objects
    ]


from analyser.packages import poetry  # noqa: F401,E402

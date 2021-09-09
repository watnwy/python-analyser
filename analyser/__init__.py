import asyncio
import logging
from functools import wraps
from typing import Awaitable, Callable, List

from analyser import models
from analyser.logging_ import analysis_logger, register_analysis_logger

logger = logging.getLogger("watnwy")

_analyses: List[Callable[[str], Awaitable[models.AnalysisEcoSystemResult]]] = []


def analysis(ecosystem="global"):
    def wrapped(f):
        @wraps(f)
        async def wrapper(
            project_path: str,
        ) -> models.AnalysisEcoSystemResult:
            register_analysis_logger(f)
            analysis_logger().debug(f"analysis {f.__module__}:{f.__name__} starts")
            ret = await f(project_path)
            analysis_logger().debug(f"analysis {f.__module__}:{f.__name__} ends")
            return models.AnalysisEcoSystemResult(name=ecosystem, objects=ret)

        _analyses.append(wrapper)
        logger.debug(f"registering analysis {f.__module__}:{f.__name__}")
        return wrapper

    return wrapped


async def run_analyses(project_path: str) -> List[models.AnalysisEcoSystemResult]:
    return [
        analysis
        for analysis in await asyncio.gather(
            *(run_analysis(project_path) for run_analysis in _analyses)
        )
    ]


from analyser.packages import pip  # noqa: F401,E402
from analyser.packages import poetry  # noqa: F401,E402

import asyncio
import concurrent.futures
import glob
import io
import os
from functools import partial
from itertools import chain
from pathlib import Path
from typing import List, cast

import aiofiles
import orjson
import yaml

from analyser import analysis, models
from analyser.logging_ import analysis_logger


async def parse_package_json(file_path: str) -> List[models.AnalysisObject]:
    async with aiofiles.open(file_path, "r") as package_json:
        package = orjson.loads(await package_json.read())
    if Path((yarn_path := f"{os.path.dirname(file_path)}/yarn.lock")).exists():
        async with aiofiles.open(yarn_path, "r") as yarn_yaml:
            yarn = yaml.load(io.StringIO(await yarn_yaml.read()))
            analysis_logger().debug(f"{yarn=}")
    return [
        models.AnalysisObject(name=package, versions=[version])
        for package, version in package.get("dependencies", {}).items()
    ]


@analysis(ecosystem="node")
async def objects_from_packages(path: str) -> List[models.AnalysisObject]:
    with concurrent.futures.ThreadPoolExecutor() as pool:
        packages_files = cast(
            List[str],
            await asyncio.get_running_loop().run_in_executor(
                pool, partial(glob.glob, f"{path}/**/package.json", recursive=True)
            ),
        )
        analysis_logger().debug(f"{packages_files=}")

    results = await asyncio.gather(
        *(
            parse_package_json(package_file)
            for package_file in packages_files
            if "node_modules" not in package_file
        )
    )

    return list(chain(*results))

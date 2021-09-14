import asyncio
import concurrent.futures
import glob
from functools import partial
from itertools import chain
from pathlib import Path
from typing import List, Optional

import aiofiles
import aiohttp
import toml

from analyser import analysis, models
from analyser.logging_ import analysis_logger

PYPI_VERSIONS_URI = "https://pypi.org/pypi/{package}/json"


async def get_version_from_filename(
    filename: str,
    package: str,
) -> Optional[str]:
    """
    Return the corresponding Pypi version for a package
    if we only have the file used for the package installation
    """
    async with aiohttp.client.ClientSession(raise_for_status=True) as session:
        response = await session.get(PYPI_VERSIONS_URI.format(package=package))
        response_json = await response.json()
        releases = response_json["releases"]

        analysis_logger().debug(
            "looking for version corresponding to file %s", filename
        )

        return next(
            (
                release
                for release, available_packages in releases.items()
                for available_package in available_packages
                if available_package["filename"] == filename
            ),
            None,
        )


async def lock_file_to_objects(lock_file: str) -> List[models.AnalysisObject]:
    async with aiofiles.open(lock_file, mode="r") as f:  # type: ignore
        content = await f.read()
        lock_content = toml.loads(content)

    async with aiofiles.open(Path(lock_file).parent.joinpath("pyproject.toml"), mode="r") as f:  # type: ignore
        content = await f.read()
        pyproject_context = toml.loads(content)

    non_transitive_packages = set(
        map(
            str.lower,
            pyproject_context.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
            .keys(),
        )
    ) | set(
        map(
            str.lower,
            pyproject_context.get("tool", {})
            .get("poetry", {})
            .get("dev-dependencies", {})
            .keys(),
        )
    )

    filtered_metadata_files = {
        package: files
        for package, files in lock_content["metadata"]["files"].items()
        if package.lower() in non_transitive_packages
    }

    versions = await asyncio.gather(
        *(
            get_version_from_filename(files[0]["file"], package)
            for package, files in filtered_metadata_files.items()
        )
    )

    return [
        models.AnalysisObject(
            name=package,
            versions=[version],
            versions_providers=[
                models.PypiReleasesVersionsProvider(
                    type="PypiReleases", package_name=package
                )
            ],
        )
        for package, version in zip(filtered_metadata_files, versions)
    ]


@analysis(ecosystem="python")
async def objects_from_packages(path: str) -> List[models.AnalysisObject]:
    with concurrent.futures.ThreadPoolExecutor() as pool:
        lock_files = await asyncio.get_running_loop().run_in_executor(
            pool, partial(glob.glob, f"{path}/**/poetry.lock", recursive=True)
        )
        analysis_logger().debug(f"{lock_files=}")

    objects = await asyncio.gather(
        *(lock_file_to_objects(str(lock_file)) for lock_file in lock_files)
    )
    analysis_logger().debug(f"{objects=}")
    return list(chain(*objects))

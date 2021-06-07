"""
Analyser that aims at finding the requirements that are defined in a setup.py pip package

Warning: This is a bit hacky.
The technique consists in monkey patching the setup.py's setup method to catch the arguments
and then interrupt the installation process as soon as possible.
"""
import asyncio
import concurrent.futures
import glob
import json
import os
import re
import sys
from functools import partial
from itertools import chain
from pathlib import Path
from typing import Iterable, List, Optional, cast

import aiofiles
import aiohttp
import wrapt
from aiofiles import os as aios

from analyser import analysis, models
from analyser.logging_ import analysis_logger

SETUP_PY_MONKEY_PATCH_SNIPPET = """
# > WATNWY_ANALYSER_PATCH

import wrapt
import setuptools
import sys
import json

def analyse_setup(wrapped, instance, args, kwargs):
    with open('./setuptools.json', 'w+') as f:
        f.write(json.dumps({
            k: v for k, v in kwargs.items()
            if k in {
                'install_requires',
                'extras_require',
                'python_requires'
            }
        }))
    sys.exit(1)

wrapt.wrap_function_wrapper(setuptools, 'setup', analyse_setup)

# < WATNWY_ANALYSER_PATCH
"""

pip_package_re = re.compile(r"\s*([\w\-_]+)((\s*[><=\-!~]+\s*[^,;\s]*\s*,?)*)\s*;?.*")
constrained_version_re = re.compile(r"^\s*==\s*([\w\.]+)$")

PYPI_CHECK_PACKAGE = "https://pypi.org/project/{package}/"


def constrained_version(constraint: str) -> Optional[str]:
    match = constrained_version_re.match(constraint)
    if match:
        return match[1]
    return None


def pip_package_to_object(pip_package: str) -> Optional[models.AnalysisObject]:
    match = pip_package_re.match(pip_package)
    if not match:
        analysis_logger().debug(f"no match {pip_package=}")
        return None

    package = match[1]
    constraints = match[2].split(",")

    version = next(
        (
            version
            for constraint in constraints
            if (version := constrained_version(constraint))
        ),
        None,
    )

    analysis_logger().debug(f"match {package=} {constraints=} {version=}")

    return models.AnalysisObject(
        name=package,
        versions=[version],
        versions_providers=[
            models.PypiReleasesVersionsProvider(
                type=models.VersionsProviderTypes.PypiReleases.value,
                package_name=package,
            )
        ],
    )


async def package_versions_providers(
    obj: models.AnalysisObject,
) -> List[models.VersionsProvider]:
    async with aiohttp.ClientSession(raise_for_status=False) as client:
        async with client.head(
            PYPI_CHECK_PACKAGE.format(package=obj.name), allow_redirects=True
        ) as response:
            package_exists_in_pypi = response.status == 200
    return (
        [
            models.PypiReleasesVersionsProvider(
                type=models.VersionsProviderTypes.PypiReleases.value,
                package_name=obj.name,
            )
        ]
        if package_exists_in_pypi
        else []
    )


async def set_versions_providers(
    objects: Iterable[models.AnalysisObject],
) -> List[models.AnalysisObject]:
    all_versions_providers = await asyncio.gather(
        *(package_versions_providers(obj) for obj in objects)
    )
    return [
        obj.copy(update={"versions_providers": versions_providers})
        for obj, versions_providers in zip(objects, all_versions_providers)
    ]


async def objects_from_setup_pys_requirements(
    setup_file_path: str,
) -> List[models.AnalysisObject]:
    analysis_logger().debug(f"{setup_file_path=}")
    project_path = os.path.dirname(setup_file_path)

    # 1. create a symlink wrapt pointing to the location of wrapt
    if (
        Path(f"{project_path}/wrapt").exists()
        and Path(f"{project_path}/wrapt").is_symlink()
    ):
        Path(f"{project_path}/wrapt").unlink()
    wrapt_location = os.path.dirname(wrapt.__file__)
    Path(f"{project_path}/wrapt").symlink_to(wrapt_location, target_is_directory=True)

    # 2. patch the setup.py with SETUP_PY_MONKEY_PATCH_SNIPPET at the beginning
    await aios.rename(setup_file_path, f"{setup_file_path}.back")

    async with aiofiles.open(f"{setup_file_path}.back", "r") as from_, aiofiles.open(
        setup_file_path, "w+"
    ) as to:
        await to.write(SETUP_PY_MONKEY_PATCH_SNIPPET)

        while read := await from_.read(1024):
            await to.write(read)

    # 3. Run python -m pip install --use-feature=in-tree-build .
    pip_install = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pip",
        "install",
        "--use-feature",
        "in-tree-build",
        project_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    await pip_install.wait()

    await aios.rename(f"{setup_file_path}.back", setup_file_path)
    Path(f"{project_path}/wrapt").unlink()

    # 4. Parse the setuptools.json
    if not Path(f"{project_path}/setuptools.json").exists():
        if pip_install.stdout:
            stdout = await pip_install.stdout.read()
            analysis_logger().error(f"{stdout=}")
        else:
            analysis_logger().warning("pip install exited with no output")
        return []

    async with aiofiles.open(f"{project_path}/setuptools.json", "r") as f:
        setuptools = json.loads(await f.read())

    Path(f"{project_path}/setuptools.json").unlink()

    analysis_logger().debug(f"{setuptools=}")

    objects_from_install_requires = [
        obj
        for package in chain(
            setuptools.get("install_requires", []),
            chain.from_iterable(setuptools.get("extras_require", {}).values()),
        )
        if (obj := pip_package_to_object(package))
    ]

    return await set_versions_providers(objects_from_install_requires)


@analysis
async def objects_from_all_setup_pys_requirements(
    project_path: str,
) -> List[models.AnalysisObject]:
    with concurrent.futures.ThreadPoolExecutor() as pool:
        setup_files = cast(
            List[str],
            await asyncio.get_running_loop().run_in_executor(
                pool, partial(glob.iglob, f"{project_path}/**/setup.py", recursive=True)
            ),
        )
        analysis_logger().debug(f"{setup_files=}")

    # We only keep root setup.py files
    setup_files = sorted(setup_files)

    roots_considered: List[str] = []
    setup_files_to_consider = []
    for setup_file in setup_files:
        if not roots_considered or roots_considered[-1] not in setup_file:
            roots_considered.append(os.path.dirname(setup_file))
            setup_files_to_consider.append(setup_file)

    analysis_logger().debug(f"{setup_files_to_consider=}")

    all_objects = await asyncio.gather(
        *(
            objects_from_setup_pys_requirements(setup_file)
            for setup_file in setup_files_to_consider
        )
    )

    return list(chain.from_iterable(all_objects))

import subprocess

import pytest

from analyser import models
from analyser.packages.poetry import objects_from_packages


@pytest.mark.asyncio
async def test_poetry(poetry_project) -> None:
    """Test that the packages added via poetry are discovered (without the transitive dependencies)"""

    # 1. Add a package via poetry
    subprocess.run("poetry add fastapi@0.65.0 -q".split(" "))

    # 2. Run our routine
    result = await objects_from_packages(".")

    # 3. Our package and only our package should be found
    assert len(result.objects) == 1
    assert result.objects[0].name == "fastapi"
    assert "0.65.0" in result.objects[0].versions
    assert result.objects[0].versions_providers is not None
    assert len(result.objects[0].versions_providers) == 1
    assert isinstance(
        result.objects[0].versions_providers[0], models.PypiReleasesVersionsProvider
    )
    assert (
        result.objects[0].versions_providers[0].type
        == models.VersionsProviderTypes.PypiReleases.value
    )
    assert result.objects[0].versions_providers[0].package_name == "fastapi"

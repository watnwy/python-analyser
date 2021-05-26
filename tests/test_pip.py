import os
from pathlib import Path

import pytest

from analyser.packages import pip


@pytest.mark.asyncio
async def test_pip() -> None:
    simple_pip_path = Path(
        os.path.dirname(os.path.abspath(__file__)) + "/projects/simple_pip"
    )
    objects = await pip.objects_from_all_setup_pys_requirements(str(simple_pip_path))

    assert len(objects) == 2
    assert objects[0].name == "click"
    assert objects[0].version is None
    assert objects[1].name == "fastapi"
    assert objects[1].version == "0.65.1"

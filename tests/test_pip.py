import os
from pathlib import Path

import pytest

from analyser.packages import pip


@pytest.mark.asyncio
async def test_pip() -> None:
    simple_pip_path = Path(
        os.path.dirname(os.path.abspath(__file__)) + "/projects/simple_pip"
    )
    result = await pip.objects_from_all_setup_pys_requirements(str(simple_pip_path))

    assert len(result.objects) == 2
    assert result.objects[0].name == "click"
    assert None in result.objects[0].versions
    assert result.objects[1].name == "fastapi"
    assert "0.65.1" in result.objects[1].versions

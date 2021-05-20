import os
import shutil
import subprocess

import pytest


@pytest.fixture(scope="function")
def poetry_project(tmpdir):
    """Initialize an empty directoty as a poetry project, cd into it, return the path"""
    current_path = os.getcwd()
    os.chdir(tmpdir)
    try:
        subprocess.run("poetry init --name='test' -n -q".split(" "))
        yield tmpdir
    finally:
        os.chdir(current_path)
        shutil.rmtree(tmpdir)

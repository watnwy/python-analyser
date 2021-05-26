from setuptools import find_packages, setup

setup(
    name="simple_pip",
    packages=find_packages(),
    install_requires=["click", "fastapi==0.65.1"],
)

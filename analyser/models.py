from enum import Enum, auto
from typing import List, Literal, Optional, Union

import orjson
from pydantic import BaseModel, Field


def orjson_dumps(v, *, default=None, **kwargs):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


class BaseModelOrjson(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):  # type: ignore
        return name


class VersionsProviderTypes(AutoName):
    PypiReleases = auto()
    GithubReleases = auto()


class GithubReleasesVersionsProvider(BaseModelOrjson):
    type: Literal[VersionsProviderTypes.GithubReleases.value]  # type: ignore
    owner: str
    repo: str


class PypiReleasesVersionsProvider(BaseModelOrjson):
    type: Literal[VersionsProviderTypes.PypiReleases.value]  # type: ignore
    package_name: str


VersionsProvider = Union[PypiReleasesVersionsProvider, GithubReleasesVersionsProvider]


class AnalysisObject(BaseModelOrjson):
    name: str
    version: Optional[str]
    versions_providers: Optional[List[VersionsProvider]] = Field(default=None)


class AnalysisEcoSystemResult(BaseModelOrjson):
    name: str = Field(default="")
    objects: List[AnalysisObject]


class PerformAnalysisRequest(BaseModelOrjson):
    path: str

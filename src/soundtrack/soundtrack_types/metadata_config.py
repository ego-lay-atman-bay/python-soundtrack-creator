from collections.abc import Mapping
from typing import Literal, TypedDict

from .common import *


class MetadataManifestConfig(TypedDict, total = False):
    file: StrPath
    title: str
    description: FileOrText
    author: str
    credits: StrPath | dict
    main_color: str
    text_color: str
    
    albums: Mapping[Literal[
        "name",
        "sort_name",
        "artist",
        "sort_artist",
    ], TagName | list[TagName]]

    tracks: Mapping[Literal[
        "links",
        "genres",
        "comment",
        "title",
    ], TagName | list[TagName]]


class CoverConfig(TypedDict, total = False):
    file: StrPath
    size: int | float | str | list | Mapping[Literal["width", "height", 'w', 'h', 'x', 'y'], int]


class Metadata(TypedDict, total = False):
    sheet = StrPath
    tracks: Mapping[Title, TrackMetadata]
    tags: Mapping[TagName, TagValue]
    cover: StrPath | CoverConfig
    manifest: MetadataManifestConfig


class MetadataSheet(TypedDict, total = False):
    file: StrPath
    ignore: list[TagName]
    map: Mapping[TagName, TagName]
    copy: Mapping[TagName, TagName]

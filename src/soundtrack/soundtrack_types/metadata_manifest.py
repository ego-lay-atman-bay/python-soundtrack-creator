from collections.abc import Mapping
from typing import Literal, TypedDict

from .common import *

class Track(TypedDict, total = False):
    title: Title
    sort_title: Title
    path: Mapping[str, StrPath]
    metadata: Mapping[TagName, TagValue]
    links: Mapping[str, URL]
    comment: str
    length: int

class Disc(TypedDict, total = False):
    number: int
    title: Title
    tracks: list[Track]

class Album(TypedDict, total = False):
    name: Title
    sort_name: Title
    artist: str
    picture: StrPath
    tracks: list[Disc]

class MetadataManifest(TypedDict, total = False):
    _version: Literal[1]
    version: int | float | str
    ia_audio_player_manifest: Literal[True]
    title: str
    description: str
    author: str
    credits: dict
    main_color: str
    text_color: str
    albums: list[Album]

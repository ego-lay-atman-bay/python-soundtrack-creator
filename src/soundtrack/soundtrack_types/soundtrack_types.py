from collections.abc import Mapping
from typing import Any, Literal, Optional, Required, TypedDict

from soundtrack.soundtrack_types.metadata_config import Metadata

from .common import *


class Effect(TypedDict, total = False):
    name: str
    options: Mapping | Any

class Track(TypedDict, total = False):
    pass

class SilenceConfig(TypedDict, total = False):
    start: Duration
    end: Duration

class FadeOptions(TypedDict, total = False):
    start: int | float
    end: int | float
    fade_adjust: int | float

class Fade(TypedDict, total = False):
    type: Literal["linear"]
    duration: Duration
    options: FadeOptions

class LoopConfig(TypedDict, total = False):
    count: int
    fade: Fade
    
class Tracks(TypedDict, total = False):
    files: StrPath | dict[Title, Track]
    type: Literal["json", "audio"]
    filename: StrPath
    effect_sheet: StrPath
    effects: list[Effect]

class SoundtrackConfig(TypedDict, total = False):
    silence: SilenceConfig
    loop: LoopConfig
    tracks: Tracks
    metadata: StrPath | Metadata
    output: StrPath
    format: str | list[str]
    ffmpeg: str | Mapping[str, str]

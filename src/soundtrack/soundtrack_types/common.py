from typing import Any
from collections.abc import Mapping

type StrPath = str
type FileOrText = str | StrPath
type URL = str | StrPath
type Title = str
type TagName = str
type TagValue = str | list[str] | int | float
type Duration = int | float
type TrackMetadata = Mapping[str, Any]
type StrColor = str

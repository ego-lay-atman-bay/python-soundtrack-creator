"""This is for creating a soundtrack from a folder using a format. The format goes as follows.

Each subdirectory includes a `track.json` file, the contents of the `track.json` file define the track title, and how it should loop (or if it should loop). The format goes as follows.

```json
{
    "track title": {
        "track": "track.wav",
        "metadata": {
            "artist": "track artist"
        }
    }
}
```

Of course the `"track"` value can be in many different formats.

```json
{
    "track": {
        "track": "file.wav"
    },
    "basic intro and loop": {
        "track": {
            "intro": "intro.wav",
            "loop": "loop.wav"
        }
    },
    "basic loop": {
        "track": {
            "loop": "loop.wav"
        }
    },
    "sample loop": {
        "track": {
            "file": "file.wav",
            "loop": "123456"
        }
    },
    "combined audio": {
        "track": [{
            "intro": "intro.wav",
            "loop": "loop.wav"
        },
        {
            "file": "drums.wav",
            "loop": "123456"
        }]
    }
}
```

The track key is used as the track title, unless specified in the `"metadata"` dictionary.
"""
import sys

import numpy
import soundfile



def main(audio: str):
    pass

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        main(args[0])

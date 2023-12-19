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
import typing
from collections import defaultdict

import logging
import sys
import os
import pathvalidate
import json5
from copy import deepcopy
import csv

from audioman import Audio
from audioman.effect import effects

from .format import format


def merge_dicts(from_, to):
    for key in from_:
        if key not in to:
            to[key] = deepcopy(from_[key])
        elif type(to[key]) != type(from_[key]) and not (
            isinstance(to[key], (int, float, str))
            and isinstance(from_[key], (int, float, str))
        ):
            raise TypeError(f"key '{key}' must be '{type(from_[key]).__qualname__}'")
        elif isinstance(to[key], dict):
            merge_dicts(from_[key], to[key])


class SoundtrackMaker:
    def __init__(self, config: str | dict) -> None:
        """Soundtrack maker

        Args:
            config (str | dict): _description_

        The config file is a json file. It can be specified either with a dict, or a path to a file. The actual json format goes as follows. Note: any duplicate keys are used to demonstrate multiple types of values it can have. You cannot have duplicates in the actual file.

        The actual file must be valid json5 format, which means you can have comments, and single quotes (and no quotes).
        ```json
        {
            "silence": { // add silence to start and / or end of track
                "start": 0.1,
                "end": 0,
            },
            "loop": { // customize the loop
                "count": 2, // how many times to loop
                "fade": { // customize the final fade
                    "function": "linear", // function to use. Currently only "linear".
                    "duration": 3, // Duration of fade.
                    "options": {
                        "start": 100, // volume to start the fade at
                        "end": 0, // volume to end the fade at
                        "fade-adjust": -100, // a value that modifies the curve
                    }
                } // The fade is similar to the adjustable fade in Audacity. Currently there is not S-Curve. If you want to quickly test it out then you can either write some code, or open Audacity.
            },
            "tracks": { // required
                "files": "path/to/folder/", // path to folder with the tracks
                "files": { // track json to specify all the tracks here
                    "title": {
                        "track": "title.wav",
                        "tags": { // track metadata
                            "artist": "Artist"
                        }
                    }
                },
                "filename": "track.json" // track json filename to search for in the "files" folder.
            },
            "metadata": "metadata.csv", // metadata spreadsheet
            "metadata": {
                "sheet": "metadata.csv", // metadata spreadsheet
                "tracks": { // track specific metadata (can also be specified in the track json)
                    "title": {
                        "track": 1
                    }
                },
                "tags": { // global metadata tags that will be filled in for every track
                    "album": "Album name",
                    "cover": "artwork.jpg",
                    "genres": ["Genre 1", "Genre 2"],
                }
            },
            "output": "path/to/folder/", // required: Output directory to place the soundtrack in
            "output": "path/to/folder/Disc {disc}/{track:02} - {title}.{format}", // output can also be a template that will be filled out with metadata for the track and file format.
            "format": "flac", // file format to export to. TODO: add file format ffmpeg options
        }
        ```

        The loop behavior goes like this. It loops the number of times specified in "count", then loops it again, but the last loop will be trimmed to the duration, and then the fade will be applied. It will look something like this with 2 loops.
        ```
        [intro][loop][loop][trimmed_faded_loop]
        ```
        """
        self.config = {}
        self.sheet = []
        self.base_path = "."

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            try:
                self.config = json5.loads(config)
            except:
                with open(config, "r") as file:
                    self.config = json5.load(file)

                self.base_path = os.path.dirname(config)

        elif hasattr(config, "read"):
            self.config = json5.load(config)
        else:
            raise TypeError("cannot open config")

        self.base_path = os.path.abspath(self.base_path)

        self.tracks: list[
            dict[
                typing.Literal[
                    "track",
                    "dir",
                ],
                dict[
                    str,
                    dict[
                        typing.Literal["track",],
                        str
                        | dict[
                            typing.Literal[
                                "intro",
                                "file",
                                "loop",
                            ],
                            str,
                        ]
                        | list[
                            typing.Literal[
                                "intro",
                                "file",
                                "loop",
                            ],
                            str,
                        ],
                    ],
                ]
                | str,
            ]
        ] = []
        
        self.audio: list[Audio] = []

        self.validate_config()

    def validate_config(self):
        if "tracks" not in self.config:
            raise KeyError("config must have tracks key")
        if "output" not in self.config:
            raise KeyError("config must have output")

        if not isinstance(self.config["tracks"], dict):
            raise ValueError("tracks must be dictionary")

        self.config["tracks"].setdefault("files", self.base_path)

        if isinstance(self.config["tracks"]["files"], str):
            if "filename" not in self.config["tracks"]:
                self.config["tracks"]["filename"] = "track.json"

        self.config.setdefault("format", "wav")

        DEFAULT_LOOP = {
            "count": 2,
            "fade": {
                "function": "linear",
                "duration": 3,
                "options": {"start": 100, "end": 0, "fade-adjust": 0},
            },
        }

        if "loop" not in self.config:
            self.config["loop"] = deepcopy(DEFAULT_LOOP)
        else:
            if not isinstance(self.config["loop"], dict):
                raise TypeError("loop must be dictionary")

            merge_dicts(DEFAULT_LOOP, self.config["loop"])

        if "silence" not in self.config or not isinstance(self.config["silence"], dict):
            self.config["silence"] = {
                "start": 0,
                "end": 0,
            }
        self.config["silence"].setdefault("start", 0)
        self.config["silence"].setdefault("end", 0)

    def start(self):
        pass

    def get_tracks(self):
        self.tracks = []

        if isinstance(self.config["tracks"]["files"], dict):
            track = {
                "track": self.config["tracks"]["files"],
                "dir": self.base_path,
            }

            self.tracks.append(track)
        elif isinstance(self.config["tracks"]["files"], str):
            parent = self.config["tracks"]["files"]
            parent = os.path.join(self.base_path, parent)

            for dir, dirs, files in os.walk(parent):
                for name in files:
                    if name.lower() != self.config["tracks"]["filename"].lower():
                        continue

                    filename = os.path.join(dir, name)
                    with open(filename, "r") as file:
                        data = json5.load(file)

                    track = {
                        "track": data,
                        "dir": os.path.dirname(filename),
                    }

                    self.tracks.append(track)

    def create_soundtrack(
        self,
    ):
        self.get_tracks()
        
        for track in self.tracks:
            self.make_track(track)

    def make_track(
        self,
        config: dict[
            typing.Literal[
                "track",
                "dir",
            ],
            dict[
                str,
                dict[
                    typing.Literal["track",],
                    str
                    | dict[
                        typing.Literal[
                            "intro",
                            "file",
                            "loop",
                        ],
                        str,
                    ]
                    | list[
                        typing.Literal[
                            "intro",
                            "file",
                            "loop",
                        ],
                        str,
                    ],
                ],
            ]
            | str,
        ],
    ):
        tracks = []

        for title in config["track"]:
            logging.info(title)
            if isinstance(config["track"][title], str):
                audio = self.make_audio(config["track"][title], config["dir"])
            elif isinstance(config["track"][title]["track"], list):
                audio = self.make_audio(config["track"][title]["track"][0], config["dir"])
                for track in config["track"][title]["track"][1::]:
                    audio = audio.merge(
                        self.make_audio(
                            track, config["dir"],
                        )
                    )
            else:
                audio = self.make_audio(config["track"][title]['track'], config['dir'])
            
            audio.tags.set('title', title)
            
            self.set_track_metadata(
                audio,
                title,
                config.get('tags', {}),
                config["dir"]
            )
            
            tracks.append(audio)
            self.save_track(audio)
            audio.unload()
        
        self.audio += tracks

    def make_audio(
        self,
        config: dict[
            typing.Literal["track",],
            str
            | dict[
                typing.Literal[
                    "intro",
                    "file",
                    "loop",
                ],
                str,
            ],
        ]
        | str,
        dir: str,
    ):
        def loop_track(intro: Audio, loop: Audio):
            audio = 0
            if intro != None:
                audio = intro

            audio += sum([loop] * self.config["loop"]["count"])

            length = loop.seconds_to_samples(self.config["loop"]["fade"]["duration"])
            fade_audio = loop.trim(length)

            fade_options = {
                "gain0": self.config["loop"]["fade"]["options"]["start"] / 100.0,
                "gain1": self.config["loop"]["fade"]["options"]["end"] / 100.0,
                "curve_ratio": self.config["loop"]["fade"]["options"]["fade-adjust"] / 100.0,
            }
            fade = effects["adjustable_fade"](
                length = fade_audio.length,
                options = fade_options,
            )

            fade_audio = fade_audio.apply_effect(fade)
            audio += fade_audio

            return audio

        if isinstance(config, str):
            file = config

            audio = Audio(os.path.join(dir, file))

        elif "file" in config or "intro" in config:
            file = config["intro"] if "intro" in config else config["file"]

            audio = Audio(os.path.join(dir, file))
            if "loop" in config:
                config["loop"] = str(config["loop"])
                if config["loop"].isnumeric():
                    intro, loop = audio.split(int(config["loop"]))
                else:
                    loop = Audio(os.path.join(dir, config["loop"]))
                    intro = audio

                audio = loop_track(intro, loop)
        elif 'loop' in config:
            config["loop"] = str(config["loop"])
            if not config["loop"].isnumeric():
                audio = Audio(os.path.join(dir, config["loop"]))
                audio = loop_track(None, audio)
            else:
                raise TypeError(f"loop '{config['loop']}' must be a file")
            
        else:
            raise NotImplementedError(f"I don't knw how to deal with this\n{config}")

        if self.config["silence"]["start"] > 0:
            audio = audio.add_silence(
                0, audio.seconds_to_samples(self.config["silence"]["start"])
            )
        if self.config["silence"]["end"] > 0:
            audio = audio.add_silence(
                -1, audio.seconds_to_samples(self.config["silence"]["end"])
            )

        return audio

    def set_track_metadata(self, track: Audio, title: str, metadata: dict[str,str], dir: str = None):
        if dir == None:
            dir = self.base_path
        
        track.tags.clear()
        track.tags['title'] = title
        track.tags.base_path = dir
        track.tags.update(metadata)
        
        if isinstance(self.config.get('metadata'), dict):
            track.tags.base_path = self.base_path
            track.tags.setdefault(self.config.get('metadata', {}).get('tracks', {}).get(title, {}))
            track.tags.setdefault(self.get_sheet_tags(track))
            track.tags.base_path = self.base_path
            track.tags.setdefault(self.config.get('metadata', {}).get('tags'))
        else:
            track.tags.setdefault(self.get_sheet_tags(track))
        
        track.tags.base_path = '.'
        
    
    def get_sheet_tags(self, track: Audio):
        if 'metadata' not in self.config:
            return {}
        file = self.config['metadata']
        if isinstance(file, dict):
            file = file.get('sheet')
        
        if file == None:
            return {}
                    
        if self.sheet == []:
        
            filename = os.path.join(self.base_path, file)
            track.tags.base_path = os.path.dirname(filename)
            
            table = []
            with open(filename, 'r', newline = '') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    table.append({key.strip() : value.strip() for key, value in row.items()})
            
            if table == []:
                return {}
            
            self.sheet = table
        else:
            table = self.sheet
        
        # this is so I can get the first key without iterating over all of them (removes unnecessary computation)
        reference = next(iter(table[0].keys()))
        
        for row in table:
            if row[reference].lower() == track.tags.get(reference).lower():
                return row
        
        return {}

    def save_audio(self):
        for audio in self.audio:
            logging.info(f"saving {audio.tags.get('title', 'UNKNOWN')}")
            self.save_track(audio)
    
    def save_track(self, track: Audio):
        # logging.info(track.tags.expand())
        tags = track.tags.expand()
        tags.setdefault('format', self.config['format'].lower())
        tags.setdefault('extension', self.config['format'].lower())

        filename = format(self.config['output'], **tags)
        logging.info(f'filename: {filename}')
        
        if filename == self.config['output']:
            filename = os.path.join(filename, track.get('title'))
        
        filename = os.path.join(self.base_path, filename)
        
        filename = pathvalidate.sanitize_filepath(filename, replacement_text=  '-')
        
        os.makedirs(os.path.dirname(filename), exist_ok = True)
        
        track.save(filename)

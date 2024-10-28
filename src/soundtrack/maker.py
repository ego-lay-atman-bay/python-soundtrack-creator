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
    },
    {
    "Complex loop": {
        "track": {
            "loop": 123456,
            "file": [{
                "file": "normal.wav",
                "play_on_loop": 1,
                "last_loop": 2,
            },
            {
                "file": "second.wav",
                "play_on_loop": 3,
            },
            "drums.wav",
            ]
        },
        "loop_count": 3
    }
}
}
```

The track key is used as the track title, unless specified in the `"metadata"` dictionary.
"""
import csv
import io
import json
import logging
import os
import pathlib
import re
import typing
from copy import copy, deepcopy
from typing import Any

import charset_normalizer
import json5
import mutagen
import mutagen.flac
import pathvalidate
from audioman import EFFECTS, Audio, AudioTags

from .format import format
from .helpers import is_float, is_int, str_to_num, read_json_file, read_text_or_file
from .soundtrack_types import (MetadataManifest, MetadataManifestConfig,
                               SoundtrackConfig, metadata_manifest)
from .soundtrack_types.common import StrPath


def normpath(path):
    return pathlib.Path(path).as_posix()


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

def read_csv(filename: str):
    table = []
    file = charset_normalizer.from_path(filename).best()
    with io.StringIO(file.output().decode(), newline = "") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            table.append({key.strip() : value.strip() for key, value in row.items()})
    
    return table

class SoundtrackMaker:
    def __init__(
        self,
        config: str | dict,
        include: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> None:
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
                    "type": "linear", // function to use. Currently only "linear".
                    "duration": 3, // Duration of fade.
                    "options": {
                        "start": 100, // volume to start the fade at
                        "end": 0, // volume to end the fade at
                        "fade_adjust": -100, // a value that modifies the curve
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
                "filename": "track.json", // track json filename to search for in the "files" folder.
                "type": "json", // Track format.
                "type": "audio", // This will grab all audio files. If there are files in "filename", then it will grab info for those. If audio files are selected without a json file, it will not loop.
                "effect_sheet": "effects.csv", // Add select effects for multiple tracks in one file.
                "effects": [{ // Effects that will be applied to every track before any other effect.
                    "name": "truncate_silence",
                }],
            },
            "metadata": "metadata.csv", // metadata spreadsheet
            "metadata": {
                "sheet": "metadata.csv", // metadata spreadsheet
                "sheet": { // filter metadata spreadsheet
                    file: "metadata.csv", // spreadsheet file
                    ignore: [ // ignore tags
                        "tag",
                    ],
                    map: { // map tags to other tags
                        "old": "new",
                    },
                    copy: { // copy tag to new tag, but also keep old tag
                        "old: "new",
                    },
                },
                "tracks": { // track specific metadata (can also be specified in the track json)
                    "title": {
                        "track": 1
                    }
                },
                "tags": { // global metadata tags that will be filled in for every track. Can be a regex pattern for the filename (without extension).
                    "album": "Album name",
                    "cover": "artwork.jpg",
                    "genres": ["Genre 1", "Genre 2"],
                    "title": ".*",
                },
                "cover": "artwork.jpg",
                "cover": {
                    "file": "artwork.jpg",
                    "size": 500, // there are many ways to define size
                    "size": "500x500",
                    "size": {
                        "width": 500,
                        "w": 500,
                        "x": 500,
                        "height": 500,
                        "h": 500,
                        "y": 500,
                    },
                }
            },
            "output": "path/to/folder/", // required: Output directory to place the soundtrack in
            "output": "path/to/folder/Disc {disc}/{track:02} - {title}.{format}", // output can also be a template that will be filled out with metadata for the track and file format.
            "format": "flac", // file format to export to
            "format": ["flac", "mp3"], // multiple formats
            "ffmpeg": "-i \"{input}\" \"{output}\"" // custom ffmpeg options
            "ffmpeg": { // custom ffmpeg options for specific format
                "flac": "-i \"{input}\" -acodec flac -compression_level 12 \"{output}\""
            }
        }
        ```

        The loop behavior goes like this. It loops the number of times specified in "count", then loops it again, but the last loop will be trimmed to the duration, and then the fade will be applied. It will look something like this with 2 loops.
        ```
        [intro][loop][loop][trimmed_faded_loop]
        ```
        """
        self.config: SoundtrackConfig = {}
        self.metadata_sheet = []
        self.effect_sheet = []
        self.include: dict[str, list[str]] = {}
        self.base_path = "."
        self.cwd = os.getcwd()
        self.dry_run = dry_run
        
        if include == None or not isinstance(include, dict):
            self.include = {}
        else:
            self.include = {str(tag).lower(): [str(v).lower() for v in value] for tag, value in include.items() if value != None}

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            try:
                self.config = json5.loads(config)
            except:
                file = charset_normalizer.from_path(config).best()
                self.config = json5.loads(file.output().decode())

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
        
        self.soundtrack_manifest: MetadataManifest = {}

        self.validate_config()

    def validate_config(self):
        if "tracks" not in self.config:
            raise KeyError("config must have tracks key")
        if "output" not in self.config:
            raise KeyError("config must have output")

        if not isinstance(self.config["tracks"], dict):
            raise ValueError("tracks must be dictionary")

        self.soundtrack_dir = self.base_path
        self.config["tracks"].setdefault("files", self.base_path)
        
        self.config['tracks'].setdefault('type', 'json')

        if isinstance(self.config["tracks"]["files"], str):
            if self.config['tracks']['type'] == 'json' and "filename" not in self.config["tracks"]:
                self.config["tracks"]["filename"] = "track.json"
            
            self.soundtrack_dir = os.path.join(self.base_path, self.config["tracks"]["files"])
        

        self.config.setdefault("format", "wav")

        DEFAULT_LOOP = {
            "count": 2,
            "fade": {
                "type": "linear",
                "duration": 3,
                "options": {"start": 100, "end": 0, "fade_adjust": 0},
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
        self.create_soundtrack()

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
                    filename = os.path.join(dir, name)
                    if self.config['tracks'].get('type', 'json') == 'audio':
                        if mutagen.File(filename) == None:
                            continue
                    elif self.config["tracks"].get("filename", None) != os.path.basename(filename):
                        continue
                    
                    if self.config["tracks"].get("filename", None):
                        try:
                            file = charset_normalizer.from_path(filename).best()
                            data = json5.loads(file.output().decode())
                        except Exception as e:
                            e.add_note(filename)
                            raise
                                
                    
                    if self.config['tracks'].get('type', 'json') == 'audio':
                        data = {
                            self.get_global_tags(filename).get('title'): {
                                "track": name,
                            }
                        }
                    
                    global_effects = []
                    
                    if isinstance(self.config['tracks'].get('effects'), list):
                        global_effects = self.config['tracks'].get('effects')
                    elif isinstance(self.config['tracks'].get('effects'), dict):
                        global_effects = [self.config['tracks'].get('effects')]
                    
                    if len(global_effects) > 0:
                        for track_info in data.values():
                            track = track_info['track']
                            if isinstance(track, str):
                                track_info['track'] = {
                                    'file': track,
                                }
                                track = track_info['track']
                            
                            track_effects = track.get('effects', [])
                            track['effects'] = global_effects + track_effects
                                            
                    track = {
                        "track": data,
                        "dir": os.path.dirname(filename),
                        "filename": filename,
                    }

                    self.tracks.append(track)

    def create_soundtrack(
        self,
    ):
        try:
            os.chdir(self.base_path)
            self.get_tracks()
            self.init_soundtrack_manifest()
            
            for track in self.tracks:
                self.make_track(track)
        finally:
            os.chdir(self.cwd)
    
    def init_soundtrack_manifest(self):
        manifest_config: MetadataManifestConfig = self.config.get('metadata', {}).get('manifest', {})
        filename = os.path.join(self.base_path, manifest_config.get('file'))
        if not filename:
            return
        if any([len(l) > 0 for l in self.include.values()]) and os.path.exists(filename):
            file = charset_normalizer.from_path(filename).best()
            self.soundtrack_manifest = json5.loads(file.output().decode())
        
        self.soundtrack_manifest.update({
            '_version': 1,
            'ia_audio_player_manifest': True,
            'version': manifest_config.get('version'),
            'title': manifest_config.get('title'),
            'author': manifest_config.get('author'),
            'main_color': manifest_config.get('main_color'),
            'text_color': manifest_config.get('text_color'),
            'description': read_text_or_file(manifest_config.get('description', ''), os.path.dirname(filename)),
            'credits': read_json_file(manifest_config.get('credits')),
        })
        self.soundtrack_manifest.setdefault('albums', [])
        
        self.save_soundtrack_manifest()
    
    def add_to_soundtrack_manifest(
        self,
        track: Audio,
        dir: StrPath,
    ):
        soundtrack_metadata_manifest = self.config.get('metadata', {}).get('manifest', {})
        
        assert isinstance(track, Audio)
        tags = track.tags
        
        tags = self.get_track_metadata(
            track.filename,
            tags.get('title'),
            tags.copy(),
            filter_tags = False,
        )
        
        used_tags: list[str] = []
        
        def get_tag(key: str | list[str], default: Any = None):
            if isinstance(key, (list, tuple, set)):
                values = {k: get_tag(k) for k in key if get_tag(k)}
                
                if len(values) == 0:
                    return default
                return values
            
            used_tags.append(tags.get_tag_name(key))
            
            return tags.get(key, default)
        
        manifest_filename = os.path.join(self.base_path, soundtrack_metadata_manifest.get('file'))
        
        album_config = soundtrack_metadata_manifest.get('albums', {})
        
        album_info = {
            'name': get_tag(
                album_config.get('album', 'album'),
                soundtrack_metadata_manifest.get('title'),
            ),
            'sort_name': get_tag(album_config.get('sort_name', 'albumsort')),
            'artist': get_tag(
                album_config.get('artist', 'albumartist'),
                soundtrack_metadata_manifest.get('author'),
            ),
            'sort_artist': get_tag(album_config.get('sort_artist', 'albumartistsort')),
            'picture': normpath(os.path.relpath(tags.picture_filename, os.path.dirname(manifest_filename))),
        }
        
        self.soundtrack_manifest.setdefault('albums', [])

        album: metadata_manifest.Album = next(filter(
            lambda a: a.get('name') == album_info['name'],
            self.soundtrack_manifest['albums'],
        ), {})
        
        for key, value in album_info.items():
            if value:
                album[key] = value
        
        disc_config = soundtrack_metadata_manifest.get('discs', {})

        disc_info = {
            "number": get_tag(
                disc_config.get('number', "disc")
            ),
            "title": get_tag(
                disc_config.get('title', "discsubtitle")
            ),
        }
        
        album.setdefault('discs', [])
        disc_data: metadata_manifest.Disc = next(filter(
            lambda a: a.get('title') == disc_info['title'],
            album['discs'],
        ), {})
        for key, value in disc_info.items():
            if value:
                if isinstance(value, (list, tuple)):
                    value = [str_to_num(i) for i in value]
                elif isinstance(value, dict):
                    value = {k: str_to_num(v) for k,v in value.items()}
                disc_data[key] = str_to_num(value)
        
        track_config = soundtrack_metadata_manifest.get('tracks', {})
        track_info = {
            "title": get_tag(
                track_config.get('title', "title")
            ),
            "sort_title": get_tag(
                track_config.get('sort_title', "titlesort")
            ),
            "artist": get_tag(
                track_config.get('artist', "artist"),
                soundtrack_metadata_manifest.get('author'),
            ),
            "track": get_tag(
                track_config.get('track', "track")
            ),
            "path": {key: normpath(os.path.relpath(value, os.path.dirname(manifest_filename))) for key, value in self.get_track_filename(track, dir).items()},
            "links": get_tag(
                track_config.get('links')
            ),
            "genres": get_tag(
                track_config.get('genres', "genres")
            ),
            "comment": get_tag(
                track_config.get('comment', "comment")
            ),
            "metadata": {key: value for key, value in tags.items() if tags.get_tag_name(key) not in used_tags},
            "length": track.samples_to_seconds(len(track)),
        }
        
        disc_data.setdefault('tracks', [])
        track_data: metadata_manifest.Album = next(filter(
            lambda a: a.get('title') == track_info['title'],
            disc_data['tracks'],
        ), {})
        
        for key, value in track_info.items():
            if value:
                if isinstance(value, (list, tuple)):
                    value = [str_to_num(i) for i in value]
                elif isinstance(value, dict):
                    value = {k: str_to_num(v) for k,v in value.items()}
                track_data[key] = str_to_num(value)
        
        if track_data not in disc_data['tracks']:
            disc_data['tracks'].append(track_data)
        print(track_data)
        
        if disc_data not in album['discs']:
            album['discs'].append(disc_data)
        
        if album not in self.soundtrack_manifest.get('albums'):
            self.soundtrack_manifest['albums'].append(album)
        
        self.save_soundtrack_manifest()
        
    def save_soundtrack_manifest(self):
        manifest_config: MetadataManifestConfig = self.config.get('metadata', {}).get('manifest', {})
        path = os.path.join(self.base_path, manifest_config.get('file'))
        if path:
            self.sort_soundtrack_manifest()
            os.makedirs(os.path.dirname(path), exist_ok = True)
            with open(path, 'w') as file:
                json.dump(self.soundtrack_manifest, file, indent = 2)

    def sort_soundtrack_manifest(self):
        self.soundtrack_manifest['albums'] = sorted(
            self.soundtrack_manifest.get('albums', []),
            key = lambda a: a.get('sort_name', a.get('name')),
        )
        
        for album in self.soundtrack_manifest['albums']:
            album: metadata_manifest.Album
            album['discs'] = sorted(
                album.get('discs', []),
                key = lambda track: track.get('number'),
            )
        
            for disc in album['discs']:
                disc: metadata_manifest.Disc
                disc['tracks'] = sorted(
                    disc.get('tracks', []),
                    key = lambda track: track.get('track'),
                )

    def make_track(
        self,
        config: dict[
            typing.Literal[
                "track",
                "dir",
                "filename",
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
        
        check_include = False
        if any([len(l) > 0 for l in self.include.values()]):
            check_include = True

        for title in config["track"]:
            if check_include:
                skip = True
                tags = self.get_track_metadata(config["filename"], title, dir = config["dir"])
                for tag, includes in self.include.items():
                    if str(tags.get(tag, '')).lower() in includes:
                        skip = False
                        break
                
                if skip:
                    continue
            
            logging.info(title)
            if isinstance(config["track"][title], str):
                audio = self.make_audio(config["track"][title], config["dir"])
            elif isinstance(config["track"][title], dict):
                if "track" not in config["track"][title]:
                    raise KeyError(f'track "{title}" does not contain "track" item')
                
                elif isinstance(config["track"][title]["track"], list):
                    audio = self.make_audio(config["track"][title]["track"][0], config["dir"])
                    for track in config["track"][title]["track"][1::]:
                        
                        try:
                            audio = audio.mix(
                                self.make_audio(
                                    track,
                                    config["dir"],
                                    config['track'][title].get('loop_count', None)
                                )
                            )
                        except KeyError as e:
                            if config.get("filename"):
                                e.add_note(config["filename"])
                            raise e
                        
                else:
                    try:
                        audio = self.make_audio(config["track"][title]['track'], config['dir'])
                    except KeyError as e:
                        if config.get("filename"):
                            e.add_note(config["filename"])
                        raise e
            audio.tags.clear()
            audio.tags.set('title', title)
            
            self.set_track_metadata(
                audio,
                title,
                config.get('tags', {}),
                config["dir"],
            )
            
            tags = audio.tags
            filename = audio.filename
            
            track_info = self.get_track_sheet_info(audio)
            effect_info = {
                "file": audio,
                "start": track_info.get('start'),
                "end": track_info.get('end'),
                "effects": []
            }
            
            if track_info.get('amplify', None) == None:
                effect_info['effects'].append({
                    "name": "amplify",
                    "options": track_info.get('amplify', 0),
                })
            
            audio = self.make_audio(effect_info, config["dir"])
            audio.filename = filename
            audio.tags = tags
            
            self.add_to_soundtrack_manifest(
                audio,
                config['dir'],
            )
            
            tracks.append(audio)
            self.save_track(audio, config['dir'])
            audio.unload()
            logging.debug(f'samples: {audio._samples}')
        
        self.audio += tracks

    def make_audio(
        self,
        config: dict[
            typing.Literal[
                "intro",
                "file",
                "loop",
                "outro",
                "start",
                "effects",
            ],
            str | int | float | list | dict,
        ] | str,
        dir: str,
        loop_count: int = 2,
    ):
        try:
            loop_count = int(config['loop_count'])
        except:
            try:
                loop_count = int(loop_count)
            except:
                try:
                    loop_count = int(self.config['loop']['count'])
                except:
                    loop_count = 2
        
        def loop_track(intro: Audio, loop: Audio, outro: Audio | None = None):
            audio = 0
            if intro != None:
                audio = intro
            

            audio += sum([loop] * loop_count)
            
            if isinstance(outro, Audio):
                audio += outro
            else:
                length = loop.seconds_to_samples(self.config["loop"]["fade"]["duration"])
                fade_audio = loop.trim(length)

                fade_options = {
                    "gain0": self.config["loop"]["fade"]["options"]["start"] / 100.0,
                    "gain1": self.config["loop"]["fade"]["options"]["end"] / 100.0,
                    "curve_ratio": self.config["loop"]["fade"]["options"]["fade_adjust"] / 100.0,
                }
                fade = EFFECTS["adjustable_fade"](
                    options = fade_options,
                )

                fade_audio = fade_audio.apply_effect(fade, length = fade_audio.length)
                audio += fade_audio

            return audio

        if isinstance(config, str):
            file = config
            
            config = {
                "file": file,
            }

            logging.debug(f'file: {os.path.join(dir, file)}')
            audio = Audio(os.path.join(dir, file))
        elif isinstance(config, dict):
            outro = None
            
            if "outro" in config:
                outro_config = deepcopy(config["outro"])
                if isinstance(outro_config, str):
                    outro_config = {
                        "file": outro_config,
                    }
                outro_config['silence'] = {
                    'start': 0,
                    'end': 0,
                }
                outro = self.make_audio(outro_config, dir, loop_count)
            
            if "file" in config or "intro" in config:
                file = config["intro"] if "intro" in config else config["file"]

                if isinstance(file, list):
                    files = file
                    audio = Audio()
                    for sub_file in files:
                        if isinstance(sub_file, str):
                            sub_file = {
                                "file": sub_file
                            }
                        
                        if 'loop' in config:
                            sub_file.setdefault('loop', config['loop'])
                            
                        audio = audio.mix(self.make_audio(sub_file, dir, loop_count))
                elif isinstance(file, dict):
                    file_config = deepcopy(file)
                    file_config['silence'] = {
                        'start': 0,
                        'end': 0,
                    }
                    audio = self.make_audio(file_config, dir, loop_count)
                elif isinstance(file, str):
                    audio = Audio(os.path.join(dir, file))
                elif isinstance(file, Audio):
                    audio = file
                    
                start = 0
                if "start" in config:
                    start_time = config["start"]
                    if is_int(str(start_time)):
                        start = int(start_time)
                    elif is_float(str(start_time)):
                        start = audio.seconds_to_samples(float(start_time))
                    
                    audio = audio.trim(start, -1)
                
                length = -1
                if "end" in config:
                    end_time = config["end"]
                    if is_int(str(end_time)):
                        length = int(end_time)
                    elif is_float(str(end_time)):
                        length = audio.seconds_to_samples(float(end_time))

                    audio = audio.trim(length - start)
                
                if "loop" in config:
                    loop_file = config["loop"]
                    if isinstance(loop_file, dict):
                        loop_config = deepcopy(loop_file)
                        loop_config['silence'] = {
                            'start': 0,
                            'end': 0,
                        }
                        loop = self.make_audio(loop_config, dir, loop_count)
                        intro = audio
                    elif isinstance(loop_file, list):
                        files = loop_file
                        loop = Audio()
                        intro = audio
                        for sub_file in files:
                            if isinstance(sub_file, str):
                                sub_file = {
                                    "file": sub_file
                                }
                            
                            if 'loop' in config:
                                sub_file.setdefault('loop', config['loop'])
                                
                            loop = loop.mix(self.make_audio(sub_file, dir, loop_count))
                    
                    elif is_int(str(loop_file)):
                        intro, loop = audio.split(int(loop_file))
                    elif is_float(str(loop_file)):
                        intro, loop = audio.split(audio.seconds_to_samples(float(loop_file)))
                    else:
                        loop = Audio(os.path.join(dir, str(loop_file)))
                        intro = audio

                    audio = loop_track(intro, loop, outro)

                elif isinstance(outro, Audio):
                    audio += outro
                    
            elif 'loop' in config:
                if not isinstance(config["loop"], (int, float)):
                    loop_config = deepcopy(config)
                    loop_config["file"] = loop_config["loop"]
                    del loop_config["loop"]
                    loop_config["silence"] = {
                        "start": 0,
                        "end": 0,
                    }
                    audio = self.make_audio(loop_config, dir, loop_count)
                    audio = loop_track(None, audio)
                else:
                    raise TypeError(f"loop '{config['loop']}' must be a file")
            else:
                e = ValueError(f"Invalid config")
                e.add_note(json5.dumps(config, indent = 2))
                raise e
            
        else:
            e = ValueError(f"Invalid config")
            e.add_note(json5.dumps(config, indent = 2))
            raise e

        config.setdefault("silence", {})
        if not isinstance(config["silence"], dict):
            config["silence"] = {}
        
        config["silence"].setdefault("end", self.config["silence"]["end"])
        config["silence"].setdefault("start", self.config["silence"]["start"])
        if config["silence"]["start"] > 0:
            audio = audio.add_silence(
                0, audio.seconds_to_samples(config["silence"]["start"])
            )
        elif config["silence"]["start"] < 0:
            audio = audio.trim(
                -audio.seconds_to_samples(config["silence"]["start"]),
                -1,
            )
        
        if config["silence"]["end"] > 0:
            audio = audio.add_silence(
                -1, audio.seconds_to_samples(self.config["silence"]["end"])
            )
        elif config["silence"]["end"] < 0:
            audio = audio.trim(
                audio.seconds_to_samples(self.config["silence"]["end"])
            )
        
        if 'effects' in config and isinstance(config['effects'], list):
            effects = config['effects']
            
            for effect_data in effects:
                if not isinstance(effect_data, dict):
                    raise TypeError('effect must be dict')
                
                if 'name' not in effect_data:
                    e = KeyError("name")
                    e.add_note('Effect must have name key')
                    raise e
                
                try:
                    effect_class = EFFECTS[effect_data["name"]]
                except KeyError as e:
                    e.add_note("effect does not exist")
                    raise
                except:
                    raise
                
                options = {}
                
                start = 0
                length = audio.length
                
                if 'options' in effect_data:
                    if not isinstance(effect_data['options'], dict):
                        if effect_class.DEFAULT:
                            options[effect_class.DEFAULT] = effect_data['options']
                        else:
                            raise ValueError(f"no default option for {effect_data['name']}")
                    else:
                        options = effect_data["options"]
                
                if 'start' in effect_data:
                    if is_int(effect_data['start']):
                        start = int(effect_data['start'])
                    elif is_float(effect_data['start']):
                        start = audio.seconds_to_samples(float(effect_data['start']))
                    
                    length = length - start
                
                if 'length' in effect_data:
                    if is_int(effect_data['length']):
                        length = int(effect_data['length'])
                    elif is_float(effect_data['length']):
                        length = audio.seconds_to_samples(float(effect_data['length']))
                    
                
                effect = effect_class(
                    options = options,
                )
                
                audio = audio.apply_effect(effect, start = start, length = length)

        return audio
    
    def get_global_tags(self, filename: str, tags: AudioTags = None):
        def fill_value(value: str):
            if isinstance(value, list):
                return [fill_value(val) for val in value]
            
            if tags:
                value = format(value, **tags.expand())
            match = re.match(value, os.path.splitext(os.path.basename(filename))[0])
            if (match):
                value = match.group()
            
            return value
        
        global_tags = self.config.get('metadata', {}).get('tags', {})
        modified_tags = {}
        for tag, value in global_tags.items():
            value = fill_value(value)
            
            modified_tags[tag] = value

        return modified_tags

    def set_track_metadata(
        self,
        track: Audio,
        title: str,
        metadata: dict[str,str],
        dir: str | None = None,
    ):
        if dir == None:
            dir = self.base_path
        
        track.tags.clear()
        if not title:
            tags = self.get_global_tags(track.filename, track.tags)
            title = tags.get('title', '')
        track.tags['title'] = title
        
        track.tags.update(metadata)
        
        track.tags.update(self.get_track_metadata(
            track.filename,
            title,
            track.tags,
            dir,
        ))
    
    def get_track_metadata(
        self,
        filename: str,
        title: str,
        tags: AudioTags | dict[str,str] | None = None,
        dir: str | None = None,
        filter_tags: bool = True,
    ) -> AudioTags:
        if dir == None:
            dir = self.base_path
        
        if tags == None:
            tags = AudioTags()
        elif not isinstance(tags, AudioTags):
            tags = AudioTags(tags)
        
        if not title:
            global_tags = self.get_global_tags(filename, tags)
            title = global_tags.get('title', '')
        tags['title'] = title
        
        if isinstance(self.config.get('metadata'), dict):
            soundtrack_metadata: dict = self.config.get('metadata', {})
            
            try:
                tags.setdefault(soundtrack_metadata.get('tracks', {}).get(title, {}))
            except Exception as e:
                e.add_note(repr(soundtrack_metadata.get('tracks', {}).get(title, {})))
                raise e

            sheet = self.get_sheet_tags(tags, filter_tags)
            tags.setdefault(sheet)
            tags.set('title', sheet.get('title', tags.get('title', '')))
            
            cover = soundtrack_metadata.get(
                'picture',
                soundtrack_metadata.get(
                    'cover',
                    soundtrack_metadata.get(
                        'artwork',
                        None,
                    ),
                ),
            )
            
            if cover:
                if isinstance(cover, dict):
                    file = cover.get('file', None)

                    if isinstance(file, str):
                        file = format(file, dir = dir, **tags.expand())
                    
                    tags.picture = file
                    
                    size = cover.get('size', None)
                    
                    if tags.picture != None and size:
                        def get_size(size: int | float | str | list | dict[str, int]) -> tuple[int, int]:
                            resize = tags.picture.size
                            picture_size = tags.picture.size
                            
                            if isinstance(size, (int, float)):
                                resize = (round(float(size)), round(float(size)))
                            elif isinstance(size, str):
                                split_size = size.split('x')
                                resize = []
                                
                                for dimension in split_size[0:2]:
                                    try:
                                        resize.append(round(float(dimension)))
                                    except:
                                        raise TypeError(f"'{dimension}' is not a number")
                                
                                if len(resize) == 0:
                                    resize = picture_size
                                elif len(resize) == 1:
                                    resize = (resize[0], resize[0])
                                else:
                                    resize = tuple(resize)
                                
                            elif isinstance(size, list):
                                w = get_size(size[0])
                                if len(size) <= 1:
                                    h = get_size(size[1])
                                else:
                                    h = w

                                resize = (w,h)
                            elif isinstance(size, dict):
                                w = size.get('width', size.get('w', size.get('x', None)))
                                h = size.get('height', size.get('h', size.get('y', None)))

                                if w == None:
                                    w = h
                                elif h == None:
                                    h = w
                                
                                if w == None:
                                    resize = picture_size
                                else:
                                    try:
                                        w = round(float(w))
                                    except:
                                        w = picture_size[0]
                                    
                                    try:
                                        h = round(float(h))
                                    except:
                                        h = picture_size[1]
                                    
                                    resize = (w,h)

                            return resize
                        
                        resize = get_size(size)
                        
                        tags.picture = tags.picture.resize(resize)
            
            if 'album' in soundtrack_metadata:
                tags.setdefault('album', soundtrack_metadata['album'])
            
            if 'genres' in soundtrack_metadata or 'genre' in soundtrack_metadata:
                tags.setdefault('genres',soundtrack_metadata.get('genres', soundtrack_metadata.get('genre', None)))
    
            tags.setdefault(self.get_global_tags(filename, tags))
        else:
            sheet = self.get_sheet_tags(tags, filter_tags)
            tags.setdefault(sheet)
            tags.set('title', sheet.get('title', tags.get('title', '')))
        
        return tags
    
    def get_sheet_tags(
        self,
        tags: AudioTags | dict[str, str],
        filter_tags: bool = True,
    ):
        if 'metadata' not in self.config:
            return {}
        file = self.config['metadata']
        if isinstance(file, dict):
            file = file.get('sheet')
        
        ignore = []
        mapping = {}
        copied = {}
        if filter_tags and isinstance(file, dict):
            ignore = file.get('ignore', [])
            mapping = file.get('map', file.get('mapping', {}))
            copied = file.get('map', file.get('copied', {}))
            file = file.get('file', None)
        
        if not isinstance(ignore, (list, tuple, set)):
            ignore = []
        if not isinstance(mapping, dict):
            raise TypeError('tag mapping needs to be dict')
        if not isinstance(copied, dict):
            raise TypeError('copied tag mapping needs to be dict')
        
        if file == None:
            return {}
                    
        if self.metadata_sheet == []:
            filename = os.path.join(self.base_path, file)
            self.metadata_sheet = read_csv(filename)
            if self.metadata_sheet == []:
                return {}
        
        table = self.metadata_sheet
        # this is so I can get the first key without iterating over all of them (removes unnecessary computation)
        reference = next(iter(table[0].keys()))
        
        sheet_tags = {}
        
        for row in table:
            if row[reference].lower() == tags.get(reference, '').lower():
                sheet_tags = row
                break
        
        sheet_tags = {key: value for key, value in sheet_tags.items() if key not in ignore}
        for old, new in mapping.items():
            value = sheet_tags.get(old)
            if old in sheet_tags:
                del sheet_tags[old]
            sheet_tags[new] = value
        
        for tag, new in copied.items():
            if tag in sheet_tags:
                sheet_tags[new] = sheet_tags[tag]
        
        return sheet_tags
    
    def get_track_sheet_info(self, track: Audio):
        file = self.config.get('tracks', {}).get('effect_sheet', None)
        if not isinstance(file, str):
            return {}
                    
        if self.effect_sheet == []:
            filename = os.path.join(self.base_path, file)
            self.effect_sheet = read_csv(filename)
            if self.effect_sheet == []:
                return {}
        
        table = self.effect_sheet
        # this is so I can get the first key without iterating over all of them (removes unnecessary computation)
        reference = next(iter(table[0].keys()))
        
        for row in table:
            if row[reference].lower() == track.tags.get(reference).lower():
                row = copy(row)
                del row[reference]
                return row
        
        return {}

    def get_track_filename(self, track: Audio, dir: str):
        self.config.setdefault('format', ['wav'])
        formats = []
        
        if isinstance(self.config['format'], str):
            formats = [self.config['format']]
        elif isinstance(self.config['format'], list):
            formats = [str(i) for i in self.config['format']]
        else:
            e = ValueError("improper format value")
            e.add_note(self.config['format'])
            raise e
        
        result: dict[str, StrPath] = {}
        
        for audio_format in formats:
            tags = track.tags.expand()
            tags['format'] = audio_format
            tags['extension'] = audio_format
            
            if dir:
                rel_dir = normpath(os.path.relpath(dir, self.soundtrack_dir))
                tags['dir'] = rel_dir

            filename = format(self.config['output'], **tags)
            
            if filename == self.config['output']:
                filename = os.path.join(filename, f"{tags.get('title', '')}.{audio_format}")
            
            filename = os.path.abspath(os.path.join(self.base_path, filename))
            filename = filename[0:3] + filename[3:].replace(':', '：').replace("?", "")
            
            filename = pathvalidate.sanitize_filepath(filename, replacement_text = '-')

            result[audio_format] = filename
        
        return result

    def save_audio(self):
        for audio in self.audio:
            logging.info(f"saving {audio.tags.get('title', 'UNKNOWN')}")
            self.save_track(audio)
    
    def save_track(self, track: Audio, dir: str | None = None):
        # logging.info(track.tags.expand())
        self.config.setdefault('format', ['wav'])
        
        formats = []
        
        if isinstance(self.config['format'], str):
            formats = [self.config['format']]
        elif isinstance(self.config['format'], list):
            formats = [str(i) for i in self.config['format']]
        else:
            e = ValueError("improper format value")
            e.add_note(self.config['format'])
            raise e
        
        _ffmpeg_options = self.config.get(
                'ffmpeg_options',
                self.config.get('ffmpeg', None),
            )
        
        ffmpeg_options = {}
        
        
        if _ffmpeg_options == None:
            _ffmpeg_options = '-i "{input}" "{output}"'
        
        if isinstance(_ffmpeg_options, str):
            for audio_format in formats:
                ffmpeg_options.setdefault(audio_format, _ffmpeg_options)
        elif isinstance(_ffmpeg_options, dict):
            ffmpeg_options = _ffmpeg_options
        else:
            e = ValueError("improper ffmpeg options")
            e.add_note(str(_ffmpeg_options))
            raise e
        
        filenames = self.get_track_filename(track, dir)
        
        for audio_format, filename in filenames.items():
            os.makedirs(os.path.dirname(filename), exist_ok = True)
            
            logging.info(f"saving {filename}")
            
            if not self.dry_run:
                track.save(
                    filename = filename,
                    ffmpeg_options = ffmpeg_options.get(audio_format, None),
                )

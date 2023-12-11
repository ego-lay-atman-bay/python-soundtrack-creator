# soundtrack-creator
Python scripts for creating a soundtrack. Can also be used to create a soundtrack from audio files ripped from a game.

Despite the fact that this repo is called `python-soundtrack-creator`, the actual module is called `soundtrack`.

- [soundtrack-creator](#soundtrack-creator)
  - [Installation](#installation)
    - [ffmpeg](#ffmpeg)
  - [Getting started](#getting-started)
  - [Creating soundtracks](#creating-soundtracks)
  - [Main config](#main-config)
  - [Track json](#track-json)
  - [Example](#example)


## Installation
This will only work on python versions >=3.8 <3.12 (`numba` doesn't support 3.12 yet).

Clone the repository
```shell
git clone https://github.com/ego-lay-atman-bay/python-soundtrack-creator.git
cd python-soundtrack-creator
```

Install the dependencies
```shell
pip install -r requirements.txt
```

### ffmpeg

You will also need ffmpeg, which can be installed with your favorite package manager.


If you are using Anaconda, install *ffmpeg* by calling

```
conda install -c conda-forge ffmpeg
```

If you are not using Anaconda, here are some common commands for different operating systems:

- ####  Linux (`apt-get`): 

```
apt-get install ffmpeg
```
or
 
```
apt-get install gstreamer1.0-plugins-base gstreamer1.0-plugins-ugly
```
- #### Linux (`yum`):
```
yum install ffmpeg
```

- #### Mac: 
```
brew install ffmpeg
```

- #### Windows: 

download ffmpeg binaries from this [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
## Getting started

Now you can run
```shell
cd src
python -m soundtrack tag -h
```

The spreadsheet is a csv file, formatted with the `,` separator, and each line is a different track. Values can be surrounded by spaces, the script trims spaces off before using the values.

The first column is used to check what file to put the rest of the metadata on.

```csv
filename   , artist  , disc
track 1.mp3, artist 1, 1
track 2    , artist 2, 2
```

The first row matches the file 'track 1.mp3' and adds the tags `{'artist':'artist 1', 'disc':'1'}`

The second row matches the file 'track 2.wav' and adds the tags `{'artist':'artist 2', 'disc':'2'}`


The first column matching is case insensitive, and if the column is `filename`, the extension may be omitted to match files of the same name, but different formats.


You can also set the first column to be a tag, so you can match track names instead.

```csv
title, composer, track
title 1, composer 1, 1
title 2, composer 2, 2
```

The first row matches a track with the title `title 1` and adds the metadata `{'composer':'composer 1', 'track': 1}`

The metadata in the spreadsheet is set after all the other metadata, so track titles can be grabbed from the filename using regex, then metadata can be added from the spreadsheet using the title for the match.

## Creating soundtracks

You can also create a soundtrack from audio files ripped from a game, specifically to automate the looping process (and make it consistent). This is a powerful tool, but it does come with one drawback, you need to spend time setting up configuration files.

The main command to run is this

```shell
python -m soundtrack create "config.json"
```

## Main config

`config.json` includes all the information needed to create the soundtrack. Here is the format it uses (in json5 syntax). Any duplicate keys here just mean that they are different types of values you can put in.

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
    "metadata": "metadata.csv", // metadata spreadsheet. Uses the same format as the `tag` command, the only difference is that there is no "filename" column, use "title" instead.
    "metadata": {
        "sheet": "metadata.csv", // metadata spreadsheet. Uses the same format as the `tag` command, the only difference is that there is no "filename" column, use "title" instead.
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

It loops the number of times specified in "count", then loops it again, but the last loop will be trimmed to the duration, and then the fade will be applied. It will look something like this with 2 loops.

```
[intro][loop][loop][trimmed_faded_loop]
```

The track json defines all the tracks in the soundtrack. These can either be defined in the main `config.json` file, or in subfolders inside the folder specified in the main `config.json`.

An example with external `track.json` files.

```json
{
  "tracks": {
    "files": "folder/",
    "filename": "track.json"
  }
}
```

with the folder structure like this

```
- folder/
  - track 1/
    - intro.wav
    - loop.wav
    - track.json
  - track 2/
    - track.wav
    - track.json
```

Alternatively, the info in the `track.json` files can be in the main `config.json` file.

```json
{
  "tracks": {
    "files": {
      "track 1": {
        "track": {
          "intro": "track 1/intro.wav",
          "loop": "track 1/loop.wav",
        }
      },
      "track 2": {
        "track": "track 2/track.wav",
      }
    }
  }
}
```

With the file structure like this

```
- track 1/
  - intro.wav
  - loop.wav
- track 2/
  - track.wav
```

## Track json

Each track needs some config to configure how the track should loop (whether it should loop), and it's metadata. Files specified in the `track.json` config files are also relative.

```json
{
	"track": {
		"track": "track.wav", // this will not loop. It can be used to use special editing, or on a track that doesn't loop.
	},
  "track 2": {
    "track": {
      "file": "track.wav",
    }
  },
	"intro + loop": {
		"track": {
			"intro": "intro.wav",
			"loop": "loop.wav",
		}
	},
	"loop": {
		"track": {
			"loop": "loop.wav",
		}
	},
	"single track loop": {
		"track": {
			"file": "track.wav",
			"loop": "05165465", // starting sample
		}
	},
	"overlay audio track": {
		"track": [{ // use a list of dictionaries to overlay tracks, like adding the drums into the track.
        "intro": "intro.wav",
        "loop": "loop.wav",
      },
      {
        "file": "drums.wav",
        "loop": "123456",
      }]
	},
  "track with metadata": { // by default this will be the track title
    "track": "track.wav",
    "tags": {
      "title": "track title", // overrides the track title
      "track": 5,
      "artist": "artist",
    }
  }
}
```

Any amount of tracks can be put into a single `track.json` file, but all of the `track.json` files inside the `"files"` folder will be used.

## Example

file structure
```
- config.json
- metadata.csv
- artwork.jpg
- tracks/
  - track 1/
    - intro.wav
    - loop.wav
    - track.json
  - track 2/
    - track.wav
    - track.json
  - track 3/
    - intro.wav
    - loop.wav
    - intro (drums).wav
    - loop (drums).wav
    - track.json
- output/
```

`config.json`

```json
{
    "silence": {
        "start": 0.1,
        "end": 0,
    },
    "loop": {
        "count": 2,
        "fade": {
            "function": "linear",
            "duration": 8,
            "options": {
                "start": 100,
                "end": 0,
                "fade-adjust": -100,
            }
        }
    },
    "tracks": {
        "files": "tracks/",
        "filename": "track.json"
    },
    "metadata": {
        "sheet": "metadata.csv",
        "tags": {
            "album": "Album name",
            "cover": "artwork.jpg",
            "genres": ["Video Games"],
        }
    },
    "output": "output/{track:02} - {title}.{format}",
    "format": "flac",
}
```

`track 1/track.json`
```json
{
  "track 1": {
    "track": {
      "intro": "intro.wav",
      "loop": "loop.wav",
    }
  }
}
```

`track 2/track.json`
```json
{
  "track 2": {
    "track": {
      "file": "track.wav",
    }
  }
}
```

`track 3/track.json`
```json
{
  "track 3": {
    "track": [{
      "intro": "intro.wav",
      "loop": "loop.wav",
    },
    {
      "intro": "intro (drums).wav",
      "loop": "loop (drums).wav",
    }]
  }
}
```

`metadata.csv`
```csv
title  ,track, artist
track 1,    1, artist
track 2,    2, artist
track 3,    3, artist 2
```

after running
```shell
python -m soundtrack create "config.json"
```

The new file structure will be
```
...
- output/
  - 01 - track 1.flac
  - 02 - track 2.flac
  - 03 - track 3.flac
```

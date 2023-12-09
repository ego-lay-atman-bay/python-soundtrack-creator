# soundtrack-creator
Python scripts for creating a soundtrack. Can also be used to create a soundtrack from audio files ripped from a game.

Despite the fact that this repo is called `python-soundtrack-creator`, the actual module is called `soundtrack`.

- [soundtrack-creator](#soundtrack-creator)
  - [Installation](#installation)
    - [ffmpeg](#ffmpeg)
  - [Getting started](#getting-started)


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

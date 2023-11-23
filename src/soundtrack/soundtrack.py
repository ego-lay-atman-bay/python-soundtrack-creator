
import logging
import sys
import argparse
import os
import pathlib
import io
import shutil
import re
from filetype import filetype
from PIL import Image
import csv


from .audioInfo import AudioInfo


class Soundtrack:
    def __init__(
        self,
        folder: str,
        output: str = None,
        album: str = None,
        title: str = None,
        track: str = None,
        artist: str = None,
        band: str = None,
        publisher: str = None,
        genre: str | list[str] = None,
        disc: int | str = None,
        cover_art: str | Image.Image = None,
        spreadsheet: str = None,
        clear: bool = False,
    ) -> None:
        self.path = folder
        self.output = output
        self.album = album
        self.title = title
        self.track = track
        self.artist = artist
        self.band = band
        self.publisher = publisher
        self.genre = genre
        self.disk = disc

        self.cover_art = cover_art
        
        self.spreadsheet = []
        self.spreadsheet_filename = spreadsheet
        self.clear = clear

        self.files = []
        self.audio: list[AudioInfo] = []

        self.read_spreadsheet()
        self.get_files()
        
    def read_spreadsheet(self):
        if not isinstance(self.spreadsheet_filename, (str)):
            return None
        
        with open(self.spreadsheet_filename, newline = '', mode = 'r') as file:
            reader = csv.DictReader(file)
            self.spreadsheet = list(reader)
    
    def get_track_csv_metadata(self, track: AudioInfo):
        if self.spreadsheet == []:
            return
        
        reference = list(self.spreadsheet[0].keys())[0]
        
        result = None
        
        def check(value: str):
            if reference.strip().lower() == 'filename':
                return os.path.basename(track.filename).lower() == value.lower() or \
                        os.path.splitext(os.path.basename(track.filename))[0].lower() == value.lower()
            
            tag_value = track.get_str_tag(reference.strip().lower())
            # logging.info(f'tag: {reference.strip().lower()}\ntag_value: {tag_value}\nvalue: {value}')
            if tag_value == None:
                return
            
            return tag_value.lower() == value.lower()
        
        for row in self.spreadsheet:
            value = row[reference].strip()
            if check(value):
                result = row
                break
        
        return result
    
    def write_track_csv_metadata(self, track: AudioInfo):
        if self.spreadsheet == []:
            return
        
        metadata = self.get_track_csv_metadata(track)
        
        logging.info(f'metadata {metadata}')
        
        if not metadata:
            return
        
        keys = list(metadata.keys())
        
        for key in metadata:
            if key == keys[0]:
                continue
            
            value = metadata[key].strip()
            tag = key.strip()
            
            logging.info(f'setting tag {tag} to {value}')
            
            track.set_tag(tag, value)
    
    def write_csv_metadata(self):
        if self.spreadsheet == []:
            return
        
        for track in self.audio:
            logging.info(f'writing csv to {os.path.basename(track.filename)}')
            self.write_track_csv_metadata(track)

    def write_tags(self):
        if self.clear:
            self.clear_tags()
        self.write_audio_titles()
        self.write_audio_album()
        self.write_artist()
        self.write_band()
        self.write_publisher()
        self.write_genre()
        self.write_disk()
        self.write_cover_art()
        self.write_csv_metadata()
    
    def clear_tags(self):
        for track in self.audio:
            track.clear()

    def get_files(self):
        self.files = []
        self.audio: list[AudioInfo] = []

        included_files = []
        
        for dir, dirnames, files in os.walk(self.path):
            for file in files:
                filename = os.path.join(dir, file)
                if os.path.isfile(filename):
                    included_files.append(file)
                logging.info(file)
                

        if isinstance(self.output, str):
            shutil.copytree(self.path, self.output, dirs_exist_ok=True)

            path = pathlib.Path(self.output)
        else:
            path = pathlib.Path(self.path)

        files = path.glob("**/**/*")
        # logging.info(list(files))
        files = [
            file for file in files if file.is_file() and file.name in included_files
        ]

        for file in files:
            audio = AudioInfo(file.as_posix())
            if audio.audio == None:
                continue

            self.files.append(file.as_posix())

            self.audio.append(audio)

    def write_audio_titles(self):
        for music in self.audio:
            if music == None:
                continue

            filename: str = os.path.basename(music.filename)

            if self.title != None:
                try:
                    title = re.search(self.title, filename).group()
                except:
                    title = self.title
                logging.info(f"{title = }")
                music.title = title

            if self.track != None:
                try:
                    track = re.search(self.track, os.path.basename(filename)).group()
                except:
                    track = self.track

                logging.info(f"{track = }")

                music.track = track

    def write_audio_album(self):
        if not isinstance(self.album, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.album = self.album

    def write_artist(self):
        if not isinstance(self.artist, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.artist = self.artist

    def write_band(self):
        if not isinstance(self.band, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.band = self.band

    def write_publisher(self):
        if not isinstance(self.publisher, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.publisher = self.publisher

    def write_genre(self):
        if not isinstance(self.genre, (str, list, tuple, set)):
            return

        if isinstance(self.genre, (list, tuple, set)):
            self.genre = ";".join(self.genre)

        for music in self.audio:
            if music == None:
                continue

            music.genre = self.genre

    def write_cover_art(self):
        image = self.cover_art

        if not isinstance(image, (str, bytes, Image.Image)):
            return

        mime = ""
        data = b""

        if isinstance(image, bytes):
            mime = filetype.guess(image).mime

        if isinstance(image, str):
            with open(image, "rb") as file:
                data = file.read()

            mime = filetype.guess(data).mime

        if isinstance(image, Image.Image):
            file = io.BytesIO()

            image.save(file, format="PNG")

            data = file.getvalue()
            mime = filetype.guess(data).mime

        for music in self.audio:
            if music == None:
                continue

            music.cover_art = data

    def write_disk(self):
        if not isinstance(self.disk, (int, str)):
            return

        for music in self.audio:
            if music == None:
                continue

            if isinstance(self.disk, str):
                try:
                    disk = re.search(
                        self.disk, os.path.basename(music.filename)
                    ).group()
                except:
                    disk = self.disk
            else:
                disk = self.disk

            music.disk = disk

    def save(self):
        for track in self.audio:
            if track == None:
                continue

            track.save()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format = '[%(levelname)s] %(message)s',
    )
    
    arg_parser = argparse.ArgumentParser(
        description = 'Fill out all the metadata in a soundtrack with this program.',
        epilog = 'Any metadata values that are not included will not be removed or modified in the audio files.'
    )
    
    arg_parser.add_argument(
        'input',
        help = 'input soundtrack folder',
    )
    
    arg_parser.add_argument(
        '--output', '-o',
        dest = 'output',
        help = 'Output folder to put the soundtrack in. If ommitted, it will modify the original files.',
    )
    
    arg_parser.add_argument(
        '--artist', '-ar',
        dest = 'artist',
        help = 'Artist or composer.',
    )
    
    arg_parser.add_argument(
        '--title', '-ti',
        dest = 'title',
        help = 'Track title. This can be regex to get the title from the filename.',
    )
    
    arg_parser.add_argument(
        '--track', '-tr',
        dest = 'track',
        help = 'Track number. This can be regex to get the track from the filename.',
    )
    
    arg_parser.add_argument(
        '--band', '-b',
        dest = 'band',
        help = 'Album artist / band',
    )

    arg_parser.add_argument(
        '--album', '-al',
        dest = 'album',
        help = 'Album title',
    )
    
    arg_parser.add_argument(
        '--publisher', '-p',
        dest = 'publisher',
        help = 'Publisher',
    )
    
    arg_parser.add_argument(
        '--genre', '-g',
        dest = 'genre',
        help = 'Genre(s)',
        nargs = '*',
    )
    
    arg_parser.add_argument(
        '--disc', '-d',
        dest = 'disc',
        help = 'Disc number. This can be regex to get the disc from the filename.',
    )
    
    arg_parser.add_argument(
        '--cover', '-c',
        dest = 'cover',
        help = 'Cover art image.',
    )
    
    arg_parser.add_argument(
        '--clear',
        dest = 'clear',
        help = 'Clear metadata before writing',
        action = 'store_true',
    )
    
    arg_parser.add_argument(
        '--spreadsheet', '-s',
        dest = 'spreadsheet',
        help = 'Add a metadata spreadsheet. This csv will have a header, and it will match the first column then add the specified metadata tags.',
    )
    
    if len(sys.argv[1:]) < 1:
        arg_parser.print_help()
        sys.exit()
    
    args = arg_parser.parse_args()
    

    soundtrack = Soundtrack(
        args.input,
        output=args.output,
        album=args.album,
        artist=args.artist,
        title=args.title,
        track=args.track,
        band=args.band,
        publisher=args.publisher,
        genre=args.genre,
        disc=args.disc,
        cover_art=args.cover,
        spreadsheet=args.spreadsheet,
        clear=args.clear,
    )

    soundtrack.write_tags()
    soundtrack.save()

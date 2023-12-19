
import logging
import os
import pathlib
import io
import shutil
import re
from filetype import filetype
from PIL import Image
import csv


from audioman import AudioTags


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
        """Auto tag all audio files in the input folder to create a soundtrack. It searches through subdirectories. If any value is `None` it will not modify that tag.

        Args:
            folder (str): Input folder. Note: it searches through subdirectories.
            output (str, optional): New output folder. This is used when you don't want to modify the original files. Defaults to None.
            album (str, optional): Album name. Defaults to None.
            title (str, optional): Title. Can be regex that searches the filename. Defaults to None.
            track (str, optional): Track number. Can be regex that searches the filename. Defaults to None.
            artist (str, optional): Artist. Defaults to None.
            band (str, optional): Band or album artist. Defaults to None.
            publisher (str, optional): Publisher or organization. Defaults to None.
            genre (str | list[str], optional): Genre. Can be list of genres. Defaults to None.
            disc (int | str, optional): Disc. Can be regex that searches the filename. Defaults to None.
            cover_art (str | Image.Image, optional): Cover art. Can be path to file, or PIL.Image.Image. Defaults to None.
            spreadsheet (str, optional): Metadata csv spreadsheet. Defaults to None.
            clear (bool, optional): Clear metadata before applying new metadata. Defaults to False.
            
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
        """
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
        print(type(self.cover_art))
        
        self.spreadsheet: list[dict[str,str]] = []
        self.spreadsheet_filename = spreadsheet
        self.clear = clear

        self.files = []
        self.audio: list[AudioTags] = []

        self.read_spreadsheet()
        self.get_files()
        
    def read_spreadsheet(self):
        """Read the spreadsheet
        """
        if not isinstance(self.spreadsheet_filename, (str)):
            return
        
        with open(self.spreadsheet_filename, newline = '', mode = 'r') as file:
            reader = csv.DictReader(file)
            self.spreadsheet = list(reader)
    
    def get_track_csv_metadata(self, track: AudioTags) -> dict[str,str] | None:
        """Get the metadata for the track from the csv spreadsheet

        Args:
            track (AudioTags): `AudioTags` track

        Returns:
            dict[str,str]: metadata
        """
        if self.spreadsheet == []:
            return
        
        reference = list(self.spreadsheet[0].keys())[0]
        
        result = None
        
        def check(value: str):
            if reference.strip().lower() == 'filename':
                return os.path.basename(track.filename).lower() == value.lower() or \
                        os.path.splitext(os.path.basename(track.filename))[0].lower() == value.lower()
            
            tag_value = track.get(reference.strip().lower())
#             logging.info(f"""track: {track}
# tag: '{reference.strip().lower()}'
# tag_value: '{tag_value}'
# value: '{value}'""")
            if tag_value == None:
                return
            
            return tag_value.lower() == value.lower()
        
        for row in self.spreadsheet:
            value = row[reference].strip()
            if check(value):
                result = row
                break
        
        return result
    
    def write_track_csv_metadata(self, track: AudioTags):
        """Write the metadata from the spreadsheet to the track.

        Args:
            track (AudioTags): `AudioTags` object.
        """
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
            
            track.set(tag, value)
    
    def write_csv_metadata(self):
        """Write the metadata from the spreadsheet to the tracks.
        """
        if self.spreadsheet == []:
            return
        
        for track in self.audio:
            logging.info(f'writing csv to {os.path.basename(track.filename)}')
            self.write_track_csv_metadata(track)

    def write_tags(self):
        """Write all the tags in the soundtrack.
        """
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
        """Clear all the tags in all the audio files.
        """
        for track in self.audio:
            track.clear()

    def get_files(self):
        """Get all the audio files in the folder. This searches subdirectories.
        """
        self.files = []
        self.audio: list[AudioTags] = []

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
            audio = AudioTags(file.as_posix())
            if audio.filename == None:
                continue

            self.files.append(file.as_posix())

            self.audio.append(audio)

    def write_audio_titles(self):
        """Write track titles.
        """
        for music in self.audio:
            if music == None:
                continue

            filename: str = os.path.basename(music.filename)
            name = os.path.splitext(filename)[0]

            if self.title != None:
                try:
                    title = re.search(self.title, name).group()
                except:
                    title = self.title
                logging.info(f"{title = }")
                music.set('title', title)

            if self.track != None:
                try:
                    track = re.search(self.track, name).group()
                except:
                    track = self.track

                logging.info(f"{track = }")

                music.set('track', track)

    def write_audio_album(self):
        """Write track album.
        """
        if not isinstance(self.album, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.set('album', self.album)

    def write_artist(self):
        """Write artist to tracks.
        """
        if not isinstance(self.artist, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.set('artist', self.artist)

    def write_band(self):
        """Write band or album artist to tracks.
        """
        if not isinstance(self.band, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.set('band', self.band)

    def write_publisher(self):
        """Write publisher or organization to tracks.
        """
        if not isinstance(self.publisher, str):
            return

        for music in self.audio:
            if music == None:
                continue

            music.set('publisher', self.publisher)

    def write_genre(self):
        """Write genre to tracks.
        """
        if not isinstance(self.genre, (str, list, tuple, set)):
            return

        if isinstance(self.genre, (list, tuple, set)):
            self.genre = ";".join(self.genre)

        for music in self.audio:
            if music == None:
                continue

            music.set('genres', self.genre)

    def write_cover_art(self):
        """Write cover art to tracks.
        """
        image = self.cover_art
        
        if image == None:
            return

        for music in self.audio:
            if music == None:
                continue
            
            music.picture = self.cover_art

    def write_disk(self):
        """Write disk to tracks.
        """
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

            music.set('disk', disk)

    def save(self):
        """Save all audio files.
        """
        for track in self.audio:
            if track == None:
                continue

            track.save()

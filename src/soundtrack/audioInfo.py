import mutagen
from mutagen import flac, id3
from PIL import Image
from filetype import filetype


import io
import typing


class AudioInfo:
    ID3_TAGS: dict[
        str, dict[typing.Literal["tag", "class", "desc"], typing.Type[id3.Frame] | str]
    ] = {
        "Picture": {"tag": "APIC", "class": id3.APIC},
        "Cover": {"tag": "APIC", "class": id3.APIC},
        "Artwork": {"tag": "APIC", "class": id3.APIC},
        "Comment": {"tag": "COMM", "class": id3.COMM},
        "Grouping": {"tag": "GRP1", "class": id3.GRP1},
        "InvolvedPeople": {"tag": "IPLS", "class": id3.IPLS},
        "MusicCDIdentifier": {"tag": "MCDI", "class": id3.MCDI},
        "MovementNumber": {"tag": "MVIN", "class": id3.MVIN},
        "MovementName": {"tag": "MVNM", "class": id3.MVNM},
        "Ownership": {"tag": "OWNE", "class": id3.OWNE},
        "PlayCounter": {"tag": "PCNT", "class": id3.PCNT},
        "Podcast?": {"tag": "PCST", "class": id3.PCST},
        "Podcast": {"tag": "PCST", "class": id3.PCST},
        "Popularimeter": {"tag": "POPM", "class": id3.POPM},
        "Private": {"tag": "PRIV", "class": id3.PRIV},
        "SynLyrics": {"tag": "SYLT", "class": id3.SYLT},
        "Album": {"tag": "TALB", "class": id3.TALB},
        "BeatsPerMinute": {"tag": "TBPM", "class": id3.TBPM},
        "BPM": {"tag": "TBPM", "class": id3.TBPM},
        "PodcastCategory": {"tag": "TCAT", "class": id3.TCAT},
        "Compilation": {"tag": "TCMP", "class": id3.TCMP},
        "Composer": {"tag": "TCOM", "class": id3.TCOM},
        "Genre": {"tag": "TCON", "class": id3.TCON},
        "Copyright": {"tag": "TCOP", "class": id3.TCOP},
        "Date": {"tag": "TDAT", "class": id3.TDAT},
        "Year": {"tag": "TDRC", "class": id3.TDRC},
        "PodcastDescription": {"tag": "TDES", "class": id3.TDES},
        "PlaylistDelay": {"tag": "TDLY", "class": id3.TDLY},
        "EncodedBy": {"tag": "TENC", "class": id3.TENC},
        "Lyricist": {"tag": "TEXT", "class": id3.TEXT},
        "FileType": {"tag": "TFLT", "class": id3.TFLT},
        "PodcastID": {"tag": "TGID", "class": id3.TGID},
        "Time": {"tag": "TIME", "class": id3.TIME},
        "Grouping": {"tag": "TIT1", "class": id3.TIT1},
        "Title": {"tag": "TIT2", "class": id3.TIT2},
        "Subtitle": {"tag": "TIT3", "class": id3.TIT3},
        "InitialKey": {"tag": "TKEY", "class": id3.TKEY},
        "PodcastKeywords": {"tag": "TKWD", "class": id3.TKWD},
        "Language": {"tag": "TLAN", "class": id3.TLAN},
        "Length": {"tag": "TLEN", "class": id3.TLEN},
        "Media": {"tag": "TMED", "class": id3.TMED},
        "OriginalAlbum": {"tag": "TOAL", "class": id3.TOAL},
        "OriginalFileName": {"tag": "TOFN", "class": id3.TOFN},
        "OriginalLyricist": {"tag": "TOLY", "class": id3.TOLY},
        "OriginalArtist": {"tag": "TOPE", "class": id3.TOPE},
        "OriginalReleaseYear": {"tag": "TORY", "class": id3.TORY},
        "FileOwner": {"tag": "TOWN", "class": id3.TOWN},
        "Artist": {"tag": "TPE1", "class": id3.TPE1},
        "Band": {"tag": "TPE2", "class": id3.TPE2},
        "Conductor": {"tag": "TPE3", "class": id3.TPE3},
        "InterpretedBy": {"tag": "TPE4", "class": id3.TPE4},
        "PartOfSet": {"tag": "TPOS", "class": id3.TPOS},
        "disk": {"tag": "TPOS", "class": id3.TPOS},
        "disc": {"tag": "TPOS", "class": id3.TPOS},
        "cd": {"tag": "TPOS", "class": id3.TPOS},
        "Publisher": {"tag": "TPUB", "class": id3.TPUB},
        "Track": {"tag": "TRCK", "class": id3.TRCK},
        "RecordingDates": {"tag": "TRDA", "class": id3.TRDA},
        "InternetRadioStationName": {"tag": "TRSN", "class": id3.TRSN},
        "InternetRadioStationOwner": {"tag": "TRSO", "class": id3.TRSO},
        "Size": {"tag": "TSIZ", "class": id3.TSIZ},
        "AlbumArtistSortOrder": {"tag": "TSO2", "class": id3.TSO2},
        "ComposerSortOrder": {"tag": "TSOC", "class": id3.TSOC},
        "ISRC": {"tag": "TSRC", "class": id3.TSRC},
        "EncoderSettings": {"tag": "TSSE", "class": id3.TSSE},
        "UserDefinedText": {"tag": "TXXX", "class": id3.TXXX},
        "Year": {"tag": "TYER", "class": id3.TYER},
        "TermsOfUse": {"tag": "USER", "class": id3.USER},
        "Lyrics": {"tag": "USLT", "class": id3.USLT},
        "CommercialURL": {"tag": "WCOM", "class": id3.WCOM},
        "CopyrightURL": {"tag": "WCOP", "class": id3.WCOP},
        "PodcastURL": {"tag": "WFED", "class": id3.WFED},
        "FileURL": {"tag": "WOAF", "class": id3.WOAF},
        "ArtistURL": {"tag": "WOAR", "class": id3.WOAR},
        "SourceURL": {"tag": "WOAS", "class": id3.WOAS},
        "InternetRadioStationURL": {"tag": "WORS", "class": id3.WORS},
        "PaymentURL": {"tag": "WPAY", "class": id3.WPAY},
        "PublisherURL": {"tag": "WPUB", "class": id3.WPUB},
        "UserDefinedURL": {"tag": "WXXX", "class": id3.WXXX},
        "TXXX": {"tag": "TXXX", "class": id3.TXXX},
        "totaldiscs": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALDISCS"},
        "totaldisks": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALDISCS"},
        "discs": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALDISCS"},
        "disks": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALDISCS"},
        "totaltracks": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALTRACKS"},
        "tracks": {"tag": "TXXX", "class": id3.TXXX, "desc": "TOTALTRACKS"},
        "encoder settings": {
            "tag": "TXXX",
            "class": id3.TXXX,
            "desc": "ENCODER SETTINGS",
        },
        "accurateripdiscid": {
            "tag": "TXXX",
            "class": id3.TXXX,
            "desc": "ACCURATERIPRESULT",
            "desc": "ACCURATERIPDISCID",
        },
        "source": {"tag": "TXXX", "class": id3.TXXX, "desc": "SOURCE"},
        "source": {"tag": "TXXX", "class": id3.TXXX, "desc": "SOURCE"},
        "encoded by": {"tag": "TXXX", "class": id3.TXXX, "desc": "ENCODED BY"},
        "encoder": {"tag": "TXXX", "class": id3.TXXX, "desc": "ENCODED BY"},
        "encoder settings": {"tag": "TXXX", "class": id3.TXXX, "desc": "ENCODER SETTINGS"},
        "encoder settings": {"tag": "TXXX", "class": id3.TXXX, "desc": "ENCODER SETTINGS"},
    }

    ID3_TAGS = {k.lower(): v for k, v in ID3_TAGS.items()}

    FLAC_TAGS: dict[str, str] = {
        "comment": "comment",
        "origin website": "origin website",
        "website": "origin website",
        "url": "origin website",
        "origin": "origin website",
        "album": "album",
        "artist": "artist",
        "display artist": "display artist",
        "composer": "composer",
        "conductor": "conductor",
        "albumartist": "albumartist",
        "album artist": "album artist",
        "band": "albumartist",
        "albumartistsort": "albumartistsort",
        "lyricist": "lyricist",
        "lyrics": "lyrics",
        "syncedlyrics": "lyrics",
        "synced lyrics": "lyrics",
        "unsyncedlyrics": "unsyncedlyrics",
        "unsynced lyrics": "unsyncedlyrics",
        "bpm": "bpm",
        "tempo": "tempo",
        "mood": "mood",
        "occasion": "occasion",
        "genre": "genre",
        "keywords": "keywords",
        "date": "date",
        "year": "year",
        "organization": "organization",
        "publisher": "organization",
        "copyright": "copyright",
        "language": "language",
        "title": "title",
        "tracktotal": "tracktotal",
        "totaltracks": "totaltracks",
        "tracks": "totaltracks",
        "tracknumber": "tracknumber",
        "track": "tracknumber",
        "discnumber": "discnumber",
        "disknumber": "discnumber",
        "disc": "discnumber",
        "disk": "discnumber",
        "totaldiscs": "totaldiscs",
        "totaldisks": "totaldiscs",
        "discs": "totaldiscs",
        "disks": "totaldiscs",
        "compilation": "compilation",
        "contentgroup": "contentgroup",
        "grouping": "contentgroup",
        "accurateripdiscid": "accurateripdiscid",
        "accurateripresult": "accurateripresult",
        "encoded by": "encoded by",
        "encoder": "encoder",
        "encoder settings": "encoder settings",
        "source": "source",
        "albumsort": "albumsort",
        "composersort": "composersort",
        "encodingtime": "encodingtime",
        "fileowner": "fileowner",
        "filetype": "filetype",
        "initial key": "initial key",
        "involvedpeoplelist": "involvedpeoplelist",
        "isrc": "isrc",
        "location": "location",
        "source medium": "source medium",
        "mixartist": "mixartist",
        "musiciancreditslist": "musiciancreditslist",
        "net radio owner": "net radio owner",
        "net radio station": "net radio station",
        "origalbum": "origalbum",
        "origartist": "origartist",
        "origfilename": "origfilename",
        "origlyricist": "origlyricist",
        "origyear": "origyear",
        "releasetime": "releasetime",
        "setsubtitle": "setsubtitle",
        "subtitle": "subtitle",
        "titlesort": "titlesort",
        "wwwartist": "wwwartist",
        "wwwaudiofile": "wwwaudiofile",
        "wwwcommercialinfo": "wwwcommercialinfo",
        "wwwcopyright": "wwwcopyright",
        "wwwpublisher": "wwwpublisher",
        "wwwradio": "wwwradio",
    }

    def __init__(self, path: str) -> None:
        """Audio info wrapper for easier and more standardized editing.

        Args:
            path (str): Path to audio file.
        """
        self.path = path

        self.audio: mutagen.FileType | flac.FLAC = mutagen.File(self.path)

    @property
    def type(self) -> typing.Literal["id3", "flac",]:
        """Audio metadata type.

        Returns:
            Literal["id3", "flac"]: Audio type: "id3" (mp3, wav), "flac" (flac)
        """
        if isinstance(self.tags, id3.ID3):
            return "id3"
        elif isinstance(self.tags, flac.VCFLACDict):
            return "flac"

        return None

    @property
    def filename(self) -> str:
        """Audio filename

        Returns:
            str: audio filename
        """
        if hasattr(self.audio, "filename"):
            return self.audio.filename
        else:
            return self.path

    @property
    def tags(self) -> id3.ID3 | flac.VCFLACDict:
        """Audio tags object created by `mutagen`

        Returns:
            id3.ID3 | flac.VCFLACDict: mutagen audio tags dict.
        """
        return self.audio.tags

    def _get_flac_tag_id(self, tag: str) -> str:
        """Get flac tag id. If it can't find the id for the tag name, it just returns the input.

        Args:
            tag (str): tag name

        Returns:
            str: tag id
        """
        return self.FLAC_TAGS.get(tag.lower(), tag)

    def _get_id3_tag_id(self, tag: str) -> str:
        """Get id3 tag id. If it can't find the id for the tag name, it just returns the input.

        Args:
            tag (str): tag name

        Returns:
            str: tag id
        """
        result = self.ID3_TAGS.get(tag.lower(), None)
        if isinstance(result, dict):
            return result["tag"]
        return tag

    def get_tag_id(self, tag: str) -> str:
        """Get audio tag id. If it can't find the id for the tag name, it just returns the input.

        Args:
            tag (str): tag name

        Returns:
            str: tag id
        """
        if self.type == "id3":
            return self._get_id3_tag_id(tag)
        elif self.type == "flac":
            return self._get_flac_tag_id(tag)

        return tag

    def _get_id3_tag_info(
        self,
        tag: str,
    ) -> dict[typing.Literal["tag", "class", "desc"], typing.Type[id3.Frame] | str]:
        """Get the id3 tag info.

        Args:
            tag (str): tag name

        Returns:
            dict[Literal["tag", "class", "desc"], Type[id3.Frame] | str]: id3 data
        
        ```python
        {
            "tag": str,
            "class": Type[id3.Frame],
            "desc": str, # (optional)
        }
        ```
        """
        result = self.ID3_TAGS.get(tag.lower(), None)
        if isinstance(result, dict):
            return result

        real_tag = tag.split(":")[0]

        for key, value in self.ID3_TAGS.items():
            if value["tag"].upper() == real_tag.upper():
                return value

    def _get_id3_tag_class(self, tag: str) -> typing.Type[id3.Frame]:
        """Get id3 tag class.

        Args:
            tag (str): tag name

        Returns:
            Type[id3.Frame]: tag class
        """
        info = self._get_id3_tag_info(tag)
        if not info:
            return
        return info["class"]

    def del_tag(self, tag: str):
        """Delete the specified tag. Does not raise exception when tag doens't exist.

        Args:
            tag (str): tag name
        """
        if self.type == 'flac':
            try:
                del self.tags[self.get_tag_id(tag)]
            except:
                pass
        elif self.type == 'id3':
            return self.tags.delall(self.get_tag_id(tag))

    def _set_flac_tag(self, tag: str, value: str | int | float | list[str]):
        """Set flac tag

        Args:
            tag (str): tag name
            value (str | int | float | list[str]): value

        Raises:
            ValueError: cannot set flac tag {tag} to {value}
        """
        try:
            self.tags[self.get_tag_id(tag)] = value
        except:
            raise ValueError(f"cannot set flac tag {tag} to {value}")

    def _set_id3_tag(self, tag: str, *args, **kwargs):
        """Set id3 tag. Arguments are passed into the id3 Frame, so if you need specific arguments, you'll have to look it up yourself.

        Args:
            tag (str): tag name
            *args (Any): id3.Frame arguments
            **kwargs (Any): id3.Frame arguments
        
        usually the `text` argument is what's needed.
        """
        try:
            tag_info = self._get_id3_tag_info(tag)
            desc = kwargs.get("desc", tag_info.get("desc", ""))
            # logging.info(desc)

            return self.tags.add(tag_info["class"](*args, desc=desc, **kwargs))
        except:
            class_ = self._get_id3_tag_class(tag)
            if not class_:
                return
            try:
                self.tags[self.get_tag_id(tag)] = class_(
                    *args, **kwargs
                )
            except:
                if not 'text' in kwargs:
                    kwargs['text'] = args[0]
                    args = args[1:]
                    self.tags[self.get_tag_id(tag)] = class_(
                        *args, **kwargs
                    )

    def set_tag(self, tag: str, *args, **kwargs):
        """Set tag.
        
        Args:
            tag (str): tag name

        Raises:
            ValueError: unknown file type

        id3 tags can take specific arguments, but flac tags just take the first argument as it's value.
        """
        if self.type == "id3":
            return self._set_id3_tag(tag, *args, **kwargs)
        elif self.type == "flac":
            value = None

            if len(args) == 0 and len(kwargs) > 0:
                value = list(kwargs.items())[0][1]
            elif len(args) > 0:
                value = args[0]

            return self._set_flac_tag(tag, value)

        raise ValueError("unknown audio file type")

    def _get_flac_tag(self, tag: str) -> str | None:
        """Get flac tag

        Args:
            tag (str): tag name

        Returns:
            str | None: tag value
        """
        return self.tags.get(self._get_flac_tag_id(tag), [None])[0]

    def _get_id3_tag(self, tag: str) -> list[id3.Frame] | id3.Frame:
        """Get id3 tag. This returns the id3.Frame object. If there are multiple id3 tags, it returns a list of all of them.

        Args:
            tag (str): tag name

        Returns:
            list[id3.Frame] | id3.Frame: list of all the id3 tags, or the only id3 tag.
        """
        value = self.tags.getall(self.get_tag_id(tag))

        if len(value) == 1:
            return value[0]

        return value

    def get_tag(self, tag: str) -> list[id3.Frame] | id3.Frame | str:
        """Get tag value. If it's an id3 tag, it returns the id3.Frame object (or list of all the tags with the tag name). If it's a flac, it just retuns the value (usually str).

        Args:
            tag (str): tag name

        Returns:
            list[id3.Frame] | id3.Frame | str: tag value
        """
        if self.type == "id3":
            return self._get_id3_tag(tag)
        elif self.type == "flac":
            return self._get_flac_tag(tag)

    def get_str_tag(self, tag: str) -> str:
        """Get tag value as a string. If it's an id3 tag, it will try to get the text. This will also only get the first instance of a tag.

        Args:
            tag (str): tag name

        Returns:
            str: tag value.
        """
        value = self.get_tag(tag)

        if isinstance(value, list):
            if len(value) == 0:
                return
            value = value[0]

        if isinstance(value, id3.Frame):
            try:
                value = value.text[0]
            except:
                value = None

        return value


    def save(self, v2_version=4, *args, **kwargs):
        """Save modified tags.

        Args:
            v2_version (int, optional): id3 v2_version. Will ignore if it's a flac file. Defaults to 4.
            *args (Any): additional parameters to pass into the save function.
            **kwargs (Any): additional parameters to pass into the save function.
        """
        try:
            self.audio.save(v2_version=v2_version, *args, **kwargs)
        except:
            self.audio.save(*args, **kwargs)

    def clear(self):
        """Clear all tags.
        """
        self.audio.clear()

    @property
    def track(self) -> float:
        """Track number

        Returns:
            float: track number
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        track = self.get_tag("track")

        if track == None:
            return

        if isinstance(track, str | int | float):
            return float(track)

        if isinstance(track, list):
            if len(track) == 0:
                return
            track = track[0]

        text = track.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @track.setter
    def track(self, track: int):
        """Set track number.

        Args:
            track (int): Track number
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(track, (list, tuple, set)):
            track = [str(track)]

        self.set_tag("track", text=list(track))

    @property
    def disk(self) -> float:
        """Disk number.

        Returns:
            float: disk number
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        disk = self.get_tag("disk")

        if disk == None:
            return

        if isinstance(disk, str | int | float):
            return float(disk)

        if isinstance(disk, list):
            if len(disk) == 0:
                return
            disk = disk[0]

        text = disk.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @disk.setter
    def disk(self, disk: int):
        """Set disk number.

        Args:
            disk (int): disk number
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(disk, (list, tuple, set)):
            disk = [str(disk)]

        self.set_tag("disk", text=list(disk))

    @property
    def disc(self) -> float:
        """Disc number.

        Returns:
            float: disc number
        
        Alias for `self.disk`
        """
        return self.disk

    @disc.setter
    def disc(self, disc):
        """Set disc number.

        Args:
            disc (int): disc number
        
        Alias for `self.disk`
        """
        self.disk = disc

    @property
    def cd(self) -> float:
        """CD number.

        Returns:
            float: CD number
            
        Alias for `self.disk`
        """
        return self.disk

    @cd.setter
    def cd(self, disk: int):
        """Set CD number.

        Args:
            cd (int): CD number
        
        Alias for `self.disk`
        """
        self.disk = disk

    @property
    def title(self) -> str:
        """Track title

        Returns:
            str: track title
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        title = self.get_tag("title")

        if title == None:
            return

        if isinstance(title, str | int | float):
            return title

        if isinstance(title, list):
            if len(title) == 0:
                return
            title = title[0]

        text = title.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @title.setter
    def title(self, title: str):
        """Track title

        Args:
            title (str): track title
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(title, (list, tuple, set)):
            title = [str(title)]

        self.set_tag("title", text=list(title))

    @property
    def album(self) -> str:
        """Album

        Returns:
            str: album
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        album = self.get_tag("album")

        if album == None:
            return

        if isinstance(album, str | int | float):
            return album

        if isinstance(album, list):
            if len(album) == 0:
                return
            album = album[0]

        text = album.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @album.setter
    def album(self, album: str):
        """Album

        Args:
            album (str): album name
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(album, (list, tuple, set)):
            album = [str(album)]

        self.set_tag("album", text=list(album))

    @property
    def publisher(self) -> str:
        """Publisher or organization.

        Returns:
            str: publisher or organization
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        publisher = self.get_tag("publisher")

        if publisher == None:
            return

        if isinstance(publisher, str | int | float):
            return publisher

        if isinstance(publisher, list):
            if len(publisher) == 0:
                return
            publisher = publisher[0]

        text = publisher.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @publisher.setter
    def publisher(self, publisher: str):
        """Publisher or organization

        Args:
            publisher (str): publisher
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(publisher, (list, tuple, set)):
            publisher = [str(publisher)]

        self.set_tag("publisher", text=list(publisher))

    @property
    def artist(self) -> str:
        """Artist

        Returns:
            str: artist
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        artist = self.get_tag("artist")

        if artist == None:
            return

        if isinstance(artist, str | int | float):
            return artist

        if isinstance(artist, list):
            if len(artist) == 0:
                return
            artist = artist[0]

        text = artist.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @artist.setter
    def artist(self, artist: str):
        """Artist

        Args:
            artist (str): artist
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(artist, (list, tuple, set)):
            artist = [str(artist)]

        self.set_tag("artist", text=list(artist))

    @property
    def band(self) -> str:
        """Band or album artist

        Returns:
            str: band or album artist
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        band = self.get_tag("band")

        if band == None:
            return

        if isinstance(band, str | int | float):
            return band

        if isinstance(band, list):
            if len(band) == 0:
                return
            band = band[0]

        text = band.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @band.setter
    def band(self, band: str):
        """Band or album artist

        Args:
            band (str): band or album artist
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(band, (list, tuple, set)):
            band = [str(band)]

        self.set_tag("band", text=list(band))

    @property
    def genre(self) -> str:
        """Genre

        Returns:
            str: genre
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        genre = self.get_tag("genre")

        if genre == None:
            return

        if isinstance(genre, str | int | float):
            return genre

        if isinstance(genre, list):
            if len(genre) == 0:
                return
            genre = genre[0]

        text = genre.text

        if isinstance(text, list) and len(text) == 1:
            try:
                text = float(text[0])
            except:
                text = text[0]

        return text

    @genre.setter
    def genre(self, genre: str):
        """Genre

        Args:
            genre (str): genre
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if not isinstance(genre, (list, tuple, set)):
            genre = [str(genre)]

        self.set_tag("genre", text=list(genre))

    @property
    def cover_art(self) -> Image.Image:
        """Cover art

        Returns:
            PIL.Image.Image: Cover art as a PIL.Image.Image object
        """
        if not isinstance(self.audio, mutagen.FileType):
            return

        if self.type == "id3":
            artwork = self.get_tag("picture")
            if isinstance(artwork, list):
                if len(artwork) == 0:
                    return
                artwork = artwork[0]

            data = artwork.data
        elif self.type == "flac":
            if len(self.audio.pictures) == 0:
                return

            artwork: flac.Picture = self.audio.pictures[0]

            data = artwork.data

        if data == b"":
            return

        file = io.BytesIO(data)
        file.seek(0)

        image = Image.open(file)

        return image

    @cover_art.setter
    def cover_art(self, image: str | bytes | Image.Image):
        """Recommend using jpeg image.

        Args:
            image (str | bytes | Image.Image): Image to set as the cover art

        Raises:
            TypeError: image must be path, bytes or PIL.Image.
        """
        if not isinstance(image, (str, bytes, Image.Image)):
            raise TypeError("image must be path, bytes or PIL.Image")

        mime = ""
        data = b""

        if isinstance(image, bytes):
            mime = filetype.guess(image).mime
            data = image

        if isinstance(image, str):
            with open(image, "rb") as file:
                data = file.read()

            mime = filetype.guess(data).mime

        if isinstance(image, Image.Image):
            file = io.BytesIO()

            image.save(file, format="JPEG")

            data = file.getvalue()
            mime = filetype.guess(data).mime

        pil_image = Image.open(io.BytesIO(data))

        if self.type == "id3":
            self.del_tag("picture")

            self.set_tag(
                "picture",
                encoding=3,  # 3 is for utf-8
                mime=mime,  # image/jpeg or image/png
                type=id3.PictureType.COVER_FRONT,  # 3 is for the cover image
                desc="Cover",
                data=data,
            )

        elif self.type == "flac":
            self.audio.clear_pictures()

            picture = flac.Picture()
            picture.data = data
            picture.type = id3.PictureType.COVER_FRONT
            picture.mime = mime
            picture.width = pil_image.width
            picture.height = pil_image.height

            self.audio.add_picture(picture)

        else:
            raise NotImplementedError(
                "I don't know how to add a picture to that audio file."
            )

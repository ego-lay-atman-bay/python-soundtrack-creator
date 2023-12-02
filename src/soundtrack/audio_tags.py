from . import _tags


import mutagen
from PIL import Image
from mutagen import id3


import io
import typing


class AudioTags(dict):
    def __init__(self, file: str = None) -> None:
        super().__init__()

        self._picture: Image.Image = None

        self.filename = None
        
        if file:
            audio = mutagen.File(file)
            self.filename = audio.filename
            if isinstance(audio.tags, id3.ID3):
                audio.tags.update_to_v24()

            keys = audio.keys()

            tags = [_tags.get_tag_name(key) for key in keys]

            for tag in tags:
                self.__setitem__(
                    tag,
                    _tags.get_tag(audio, tag),
                )

    def save(self, file: str = None):
        if file == None and self.filename != None:
            file = self.filename
        else:
            raise AttributeError('must provide file')
        
        audio: mutagen.FileType = mutagen.File(file)
        if isinstance(audio.tags, id3.ID3):
            audio.tags.update_to_v24()

        if audio.tags == None:
            audio.add_tags()

        audio.tags.clear()

        for tag in self:
            _tags.set_tag(audio, tag, self[tag])

        _tags.set_picture(audio, self.picture)

        audio.save(file)

    def __setitem__(self, key: str, value: str | list) -> None:
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        if key == 'picture':
            self.picture = value
            return

        return super().__setitem__(key, value)
    
    def set(self, key: str, value: str | list) -> None:
        return self.__setitem__(key, value)

    def __getitem__(self, key: str) -> str | list:
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        return super().__getitem__(key)

    def get(self, key: str, default = None):
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        return super().get(key, default)

    def __contains__(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        return super().__contains__(key)

    def pop(self, key: str, default: typing.Any):
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        return super().pop(key, default)

    def setdefault(self, key: str, default: str):
        if not isinstance(key, str):
            raise TypeError('key must be str')

        key = key.lower()
        key = _tags.get_tag_name(key)

        return super().setdefault(key, default)

    @property
    def picture(self) -> Image.Image | None:
        return self._picture
    @picture.setter
    def picture(self, image: Image.Image | str | bytes | io.BytesIO | None):
        if image == None:
            picture = None
        elif isinstance(image, str) or (hasattr(image, 'read') and hasattr(image, 'seek') and hasattr(image, 'tell')):
            picture = Image.open(image)
        elif isinstance(image, bytes):
            picture = Image.open(io.BytesIO(image))
        elif isinstance(image, Image.Image):
            picture = image.copy()
        else:
            raise TypeError('could not load image')

        self._picture = picture

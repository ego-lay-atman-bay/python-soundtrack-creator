from . import _tags


import os
import mutagen
import PIL
from PIL import Image
from mutagen import id3


import io
import typing


class AudioTags(dict):
    def __init__(self, file: str = None) -> None:
        super().__init__()
        self.base_path: str = '.'

        self._picture: Image.Image = None

        self.filename = None
        self.load(file)
        
    def load(self, file: str = None):
        if file == None:
            file = self.filename
        
        self.clear()
        
        self.filename = None
        
        if file:
            audio = mutagen.File(file)
            if audio == None:
                return
            
            self.filename = audio.filename
            if isinstance(audio.tags, id3.ID3):
                audio.tags.update_to_v24()

            keys = audio.keys()

            tags = [_tags.get_tag_name(key) for key in keys]

            for tag in tags:
                if tag == 'picture':
                    continue
                
                self.__setitem__(
                    tag,
                    _tags.get_tag(audio, tag),
                )
            
            self.picture = _tags.get_picture(audio)

    def save(self, file: str = None):
        if file == None and self.filename != None:
            file = self.filename
        else:
            if file == None:
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

        try:
            audio.save(file, v2_version = 4)
        except:
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

    def setdefault(self, key: str, default: str = None):
        if not isinstance(key, (str, dict, list)):
            raise TypeError('key must be str')
        
        if isinstance(key, dict):
            for tag in key:
                self.setdefault(tag, key[tag])
            return
        elif isinstance(key, list):
            for tag in key:
                self.setdefault(tag[0], tag[1])
            return

        key = key.lower()
        key = _tags.get_tag_name(key)
        
        if key not in self:
            self.__setitem__(key, default)
        
        return self.get(key)

    
    def update(self, values: dict | typing.Iterable[tuple], **kwargs):
        if isinstance(values, dict):
            for key in values:
                self.__setitem__(key, values[key])
        elif isinstance(values, list):
            for item in values:
                self.__setitem__(item[0], item[1])
        for key in kwargs:
            self.__setitem__(key, kwargs[key])
    
    def expand(self):
        tags = dict()
        for tag in self:
            for name in _tags.get_tag_names(tag):
                tags[name] = self[tag]
        
        return tags

    @property
    def picture(self) -> Image.Image | None:
        return self._picture
    @picture.setter
    def picture(self, image: Image.Image | str | bytes | io.BytesIO | None):
        try:
            if image == None:
                picture = None
            elif isinstance(image, str) or (hasattr(image, 'read') and hasattr(image, 'seek') and hasattr(image, 'tell')):
                if isinstance(image, str):
                    image = os.path.join(self.base_path, image)
                picture = Image.open(image)
            elif isinstance(image, bytes):
                image = io.BytesIO(image)
                image.seek(0)
                picture = Image.open(image)
            elif isinstance(image, Image.Image):
                picture = image.copy()
            else:
                picture = None
        except PIL.UnidentifiedImageError:
            picture = None

        self._picture = picture

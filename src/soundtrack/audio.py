import typing

import os
import numpy
import soundfile

from .effect import Effect

class Audio:
    def __init__(self, file: str | numpy.ndarray = numpy.array([]), sample_rate: int = None) -> None:        
        self.samples: numpy.ndarray = None
        self.filename: str = ''
        
        if isinstance(file, str):
            self.filename = file
            self.read()
            if sample_rate != None:
                self.sample_rate = sample_rate
        elif isinstance(file, numpy.ndarray):
            if sample_rate == None:
                sample_rate = 44000
                
            self.sample_rate = sample_rate
            
            self.samples: numpy.ndarray = file.copy()
            
        
        
    def read(self, filename: str = None):
        if not filename == None:
            self.filename = filename
        
        if not os.path.exists(self.filename):
            raise FileNotFoundError('file not found')
        if os.path.isdir(self.filename):
            raise IsADirectoryError('path is a directory, not a file')
        
        audio, self.sample_rate = soundfile.read(self.filename, always_2d = True)
        self.samples = audio.swapaxes(1,0)
        self.channels = self.samples.shape[0]
    
    def save(self, filename: str = None):
        if filename != None:
            self.filename = filename
        
        if isinstance(self.filename, str):
            soundfile.write(self.filename, self.samples.swapaxes(1, 0), samplerate = self.sample_rate)
    
    def to_samples(self, duration: float, sample_rate: int = None) -> int:
        """Convert seconds to samples.

        Args:
            duration (float): Duration in seconds.
            sample_rate (int, optional): Sample rate. Defaults to `Audio.sample_rate`.

        Returns:
            int: duration in samples
        """
        if sample_rate == None:
            sample_rate = self.sample_rate
        
        return int(duration * sample_rate)
    
    def trim(self, start: int = 0, length: int = 1):
        end = start + length
        
        samples = self.samples.swapaxes(1,0)[start:end].swapaxes(1,0)
        return Audio(samples, sample_rate = self.sample_rate)
    
    def apply_effect(self, effect: Effect, start: int = 0):
        """Apply effect.

        Args:
            effect (Effect): Effect to apply to audio. This effect must be an object that inherits from the `Effect` class.
            start (int, optional): Where to start the effect in the audio in samples. Defaults to 0.

        Returns:
            Audio: New Audio with applied effect.

        Raises:
            TypeError: effects must inherit from the Effect class
        """
        if not isinstance(effect, Effect):
            raise TypeError('effects must inherit from the Effect class')
        
        return self.apply_scaler(effect.get(), start = start)
    
    def apply_scaler(self, scaler: numpy.ndarray, start: int = 0):
        """Apply a scaler to the audio samples.

        Args:
            scaler (numpy.ndarray): Scaler to apply to the audio samples.
            start (int, optional): Where to apply the scaler in samples. Defaults to 0.
        
        Returns:
            Audio: New Audio with applied scaler
        """
        samples = self.samples.copy()

        length = len(scaler)
        end = start + length

        for channel in samples:
            channel[start:end] = channel[start:end] * scaler
        
        return Audio(samples, sample_rate = self.sample_rate)
    
    def __add__(self, value: int | float):
        if not isinstance(value, (int, float, Audio)):
            return self + value

        if isinstance(value, Audio):
            if value.samples.shape[0] != self.samples.shape[0]:
                raise TypeError('cannot add audio with different number of channels')
            
            samples = numpy.append(self.samples, value.samples, axis = 1)
            
            audio = Audio(samples, sample_rate = self.sample_rate)
            return audio
        
        if isinstance(value, (int, float)):
            samples = self.samples + value
            
            audio = Audio(samples, sample_rate = self.sample_rate)
            return audio
    
    def __radd__(self, value: int | float):
        return self.__add__(value)
    
    def __sub__(self, value: float | int):
        if isinstance(value, Audio):
            raise TypeError('cannot subtract Audio from each other')
        if isinstance(value, (float, int)):
            samples = self.samples - value
            return Audio(samples, sample_rate = self.sample_rate)
    
    def __rsub__(self, value: float | int):
        return self.__sub__(value)
    
    def convert_to_sample_rate(self, sample_rate: int):
        """I want this to be able to convert a sound to a different sample rate without changing how it sounds. However, right now it just sets the sample rate without changing the samples.

        Args:
            sample_rate (int): new sample rate

        Raises:
            TypeError: sample_rate must be 'int'
            ValueError: sample_rate must be greater than 0
        """
        if not isinstance(sample_rate, int):
            raise TypeError("sample_rate must be 'int'")
        if sample_rate < 1:
            raise ValueError("sample_rate must be greater than 0")
        
        self.sample_rate = sample_rate
    
    @property
    def length(self):
        return self.__len__()
    
    def __len__(self):
        return self.samples.shape[1]

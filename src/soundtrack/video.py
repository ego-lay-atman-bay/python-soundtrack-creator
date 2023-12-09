import logging

import typing
import os
import subprocess
import math
import time
import re
import pydub
from PIL import Image, ImageDraw, ImageFont

from .audio_info import AudioInfo

ffmpeg_log_filename = 'ffreport.log'

TIMESTAMP_RE_PATTERN = r'(?P<H>[+-]?[.]?[0-9]+[.]?[0-9]*([e][+-]?[0-9]+)?):(?P<M>[+-]?[.]?[0-9]+[.]?[0-9]*([e][+-]?[0-9]+)?):(?P<S>[+-]?[.]?[0-9]+[.]?[0-9]*([e][+-]?[0-9]+)?)'
TIMESTAMP_RE = re.compile(TIMESTAMP_RE_PATTERN)

def setup_ffmpeg_log(filename = ffmpeg_log_filename, level = 32):
    """Setup ffmpeg logging.

    Args:
        filename (str, optional): Output log. Defaults to 'ffmpeg.log'.
        level (int, optional): Log level. Levels are defined at https://ffmpeg.org/ffmpeg.html#toc-Generic-options. Defaults to 32 (info).
    """
    os.environ['FFREPORT'] = f'file={filename}:level={level}'


def create_timestamp(time_in_seconds):
    hours, remainder = divmod(time_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{hours:.0f}:{minutes:02.0f}:{seconds:02.0f}'

class VideoSoundtrack():
    def __init__(self, folder : str, output : str, image : str = None, time_offset = 0, sample_rate = 44000) -> None:
        self.input = folder
        self.output = output
        self.audio_output = os.path.splitext(self.output)[0] + '.wav'
        self.timestamps_output = os.path.splitext(self.output)[0] + '-timestamps.txt'
        self.video_export_ffconcat_path = os.path.splitext(self.output)[0] + '.ffconcat'
        self.sample_rate = sample_rate

        self.image = None
        if image:
            self.image = Image.open(image)

        self.font = ImageFont.truetype('arialbd.ttf', 85)
        self.text_color = 'white'
        self.stroke_color = '#0e5f9aff'
        self.stroke_width = 10

        self.duration_seconds = 0
        self.time_offset = time_offset

        self.music : list[dict[typing.Literal['tags', 'audio'], AudioInfo | pydub.AudioSegment]] = []
        self.audio_track : pydub.AudioSegment = pydub.AudioSegment.empty()
        self.audio_track = self.audio_track.set_frame_rate(self.sample_rate)
        self.timestamps : list[dict[
            typing.Literal[
                'timestamp',
                'duration_seconds',
                'tags'
            ], str | float | AudioInfo
        ]] = []
        self.images : list[dict[
            typing.Literal[
                'image_path',
                'timestamp',
                'duration_seconds',
                'tags',
            ], str | float | AudioInfo
        ]] = []
        
    def start(self):
        self.get_files()
        self.combine_audio()
        self.export_timestamps()
        
        self.export_audio()

        self.generate_images()
        self.create_video()

    def get_files(self):
        self.music = []

        logging.info('getting files')
        for dir, subdir, files in os.walk(self.input):
            for file in files:
                music = {}
                path = os.path.join(dir, file)
                music['tags'] = AudioInfo(path)
                logging.info(f"{music['tags'].disk}-{music['tags'].track} - {music['tags'].title}")
                if music['tags'].audio != None:
                    self.music.append(music)

        logging.info('sorting')
        self.music = sorted(self.music, key = lambda x: [x['tags'].disk, x['tags'].track], reverse = False)

    def combine_audio(self):
        logging.info('combining audio')

        self.audio_track : pydub.AudioSegment = pydub.AudioSegment.empty()

        for track in self.music:
            logging.info(f"{track['tags'].title}")
            audio : pydub.AudioSegment = pydub.AudioSegment.from_file(track['tags'].filename)

            audio = audio.set_frame_rate(self.sample_rate)

            self.audio_track += audio


            time = (len(self.audio_track) - len(audio)) / 1000
            time += self.time_offset

            timestamp = {
                'timestamp': create_timestamp(time),
                'duration_seconds': len(audio) / 1000,
                'tags': track['tags'],
            }
            logging.info(f'{time} - {timestamp["timestamp"]} - {timestamp["tags"].title}')
            self.timestamps.append(timestamp)

            del audio

        logging.info(f'end: {self.audio_track.duration_seconds}')

        self.duration_seconds = self.audio_track.duration_seconds
        self.full_duration = self.duration_seconds + self.time_offset
    
    def export_audio(self):
        logging.info('exporting audio')
        self.audio_track.export(self.audio_output)
        logging.info(f'exported audio to {self.audio_output}')

        # deallocate audio from memory
        self.audio_track = None
        
    def generate_images(self):
        logging.info('generating images')
        self.images = []
        
        background = 'black'
        size = (1920, 1080)
        pos = (50, 820)

        base_image = Image.new('RGBA', size, color = 'black')
        image = self.image.copy()
        x_scale = size[0] / image.size[0]
        y_scale = size[1] / image.size[1]
        
        scale = max(x_scale, y_scale)

        new_size = (
            math.floor(image.size[0] * scale),
            math.floor(image.size[1] * scale),
        )

        image = image.resize(new_size)
        base_image.paste(
            image,
            (
                math.floor((base_image.size[0] / 2) - (image.size[0] / 2)),
                math.floor((base_image.size[1] / 2) - (image.size[1] / 2)),
            )
        )

        for track in self.timestamps:
            tags = track['tags']
            text = f'Disc {tags.disc:.0f} / {tags.track:.0f}\n{tags.title}'

            image_path = os.path.join(os.path.dirname(self.output), 'images', f"{tags.track:02.0f} - {tags.title}.png")
            
            logging.info(f'{text}')

            track_image = base_image.copy()
            draw_image = ImageDraw.Draw(track_image)

            draw_image.multiline_text(
                pos,
                text = text,
                font = self.font,
                fill = self.text_color,
                stroke_width = self.stroke_width,
                stroke_fill = self.stroke_color,
            )
            
            os.makedirs(os.path.dirname(image_path), exist_ok = True)
            track_image.save(image_path)

            image_info = {
                'image_path': image_path,
                'timestamp': track['timestamp'],
                'duration_seconds': track['duration_seconds'],
                'tags': tags,
            }
            self.images.append(image_info)
    
    def create_video(self):
        setup_ffmpeg_log(ffmpeg_log_filename)
        logging.info('creating video')
        start = 0
        args = ['ffmpeg', '-y', '-safe', '0']
        # filter_complex = []
        # 
        # inputs = []
        
        ffconcat = 'ffconcat version 1.0\n'
        
        index = 0
        for image in self.images:
            path = image['image_path'].replace(
                "'", r"'\''",
            )
            path = os.path.relpath(path, os.path.dirname(self.output))
            ffconcat += f"file '{path}'\n"
            ffconcat += f"duration {image['duration_seconds']}\n"
            # image_input = [
            #     '-loop', '1',
            #     '-t', str(image['duration_seconds']),
            #     '-i', image['image_path'],
            # ]
            # inputs.append(image_input)
            # args += image_input
            
            # filter_complex.append(f'[{index}:v]')
            index += 1
            
        ffconcat += f"file '{path}'\n"
        
        # filter_complex.append(f'concat=n={len(inputs)}:v=1')
        # filter_complex.append('[v]')
        
        # args.append(' '.join(filter_complex))
        
        # logging.debug(f'filter_complex:\n{args[-1]}')
        
        # args += ['-map', "[v]", '-c:v', 'libx264', '-vf', 'fps=30', '-pix_fmt', 'yuv1080p', self.output]
        
        logging.debug(f'{self.video_export_ffconcat_path}\n\n{ffconcat}')
        
        # with open(self.video_export_ffconcat_path, 'w') as file:
        #     file.write(ffconcat)
        
        with open(self.video_export_ffconcat_path, 'w') as file:
            file.write(ffconcat)
        
        args += [
            '-i', self.video_export_ffconcat_path,
            '-i', self.audio_output,
            '-c:a', 'copy',
            '-vf', 'fps=30',
            self.output,
        ]
        
        logging.debug(f'output_args:\n{args}')
        
        start_time = time.time()
        
        result = subprocess.run(
            args,
        )
        
        with open(ffmpeg_log_filename, 'r') as file:
            logging.info(f'ffmpeg output\n\n{file.read()}\n')
        
        end_time = time.time()
        logging.info(f'finished in {create_timestamp(end_time - start_time)}')
        if result.returncode > 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                result.stdout,
                result.stderr,
            )
        
        
        logging.info(f'exported video to {self.output}')
        
        #     image_array = numpy.array(image['image'])
        #     clip : movie.ImageClip = movie.ImageClip(
        #         image_array,
        #     ).set_duration(
        #         image['duration_seconds'],
        #     ).set_start(
        #         start
        #     )
        #     
        #     clips.append(clip)

        # self.video : movie.CompositeVideoClip = movie.CompositeVideoClip(
        #     clips,
        # ).set_fps(30)
        
        # audio = movie.AudioFileClip(self.audio_output, fps = self.sample_rate)
        
        # self.video.write_videofile(self.output)

    def export_timestamps(self):
        timestamps = ''
        
        for timestamp in self.timestamps:
            timestamps += f"{timestamp['timestamp']} - {timestamp['tags'].title}\n"
    
        # timestamps += f'\n{self.full_duration}'
        
        os.makedirs(os.path.dirname(self.timestamps_output), exist_ok = True)
        
        with open(self.timestamps_output, 'w') as file:
            file.write(timestamps)
    
    def update_timestamps_file(self):
        with open(self.timestamps_output, 'r') as file:
            timestamps = file.read()
        
        timestamp_tracks = timestamps.splitlines()
        
        timestamp_line_re = re.compile(r'(?P<time>.*) - (?P<title>.*)')
        
        offset = 0
        
        line = timestamp_tracks[0]
        found = timestamp_line_re.match(line)
        
        if found:
            groups = found.groupdict()
            timestamp = groups['time']
            title = groups['title']
            
            original_offset = self.timestamp_to_seconds(timestamp)
            offset =  self.time_offset - original_offset
        
        for index in range(len(timestamp_tracks)):
            line = timestamp_tracks[index]
            found = timestamp_line_re.match(line)
            
            if not found:
                break
            
            groups = found.groupdict()
            timestamp = groups['time']
            title = groups['title']
            
            seconds = self.timestamp_to_seconds(timestamp)
            seconds += offset
            
            new_timestamp = create_timestamp(seconds)
            timestamp_tracks[index] = f'{new_timestamp} - {title}'
        
        with open(self.timestamps_output, 'w') as file:
            file.write('\n'.join(timestamp_tracks))
        
    def timestamp_to_seconds(self, timestamp : str):
        split_time = self.split_timestamp(timestamp)
        return self.time_to_seconds(split_time)
    
    def split_timestamp(self, timestamp : str):
        found = TIMESTAMP_RE.match(timestamp)
        
        if not found:
            return (0,0,0)

        groups = found.groupdict()
        
        return (
            float(groups['H']),
            float(groups['M']),
            float(groups['S']),
        )
        
    def time_to_seconds(self, _time : tuple[float, float, float]):
        seconds = _time[2]
        seconds += _time[1] * 60
        seconds += _time[0] * 3600
        
        return seconds

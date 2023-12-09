import sys
import argparse
import logging
import numpy
from .soundtrack import Soundtrack
from .maker import SoundtrackMaker

def setup_logger(level = logging.INFO):
    if isinstance(level, str):
        level = logging._nameToLevel.get(level.upper(), logging.INFO)
    
    logging.basicConfig(
        level = level,
        format = '[%(levelname)s] %(message)s',
    )
    logging.captureWarnings(True)
    numpy.seterr(all = 'warn')


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description = 'Fill out all the metadata in a soundtrack with this program.',
        epilog = 'Any metadata values that are not included will not be removed or modified in the audio files.'
    )
    
    arg_parser.add_argument(
        '--log_level', '-l',
        dest = 'log_level',
        help = f'log level {{{", ".join(logging._nameToLevel.keys())}}}',
        default = logging.INFO,
        
    )
    
    subparsers = arg_parser.add_subparsers(
        title = 'commands',
        dest = 'command',
    )
    
    tag = subparsers.add_parser(
        'tag',
        help = 'add metadata to a soundtrack',
    )
    
    tag.add_argument(
        'input',
        help = 'input soundtrack folder',
    )
    
    tag.add_argument(
        '--output', '-o',
        dest = 'output',
        help = 'Output folder to put the soundtrack in. If ommitted, it will modify the original files.',
    )
    
    tag.add_argument(
        '--artist', '-ar',
        dest = 'artist',
        help = 'Artist or composer.',
    )
    
    tag.add_argument(
        '--title', '-ti',
        dest = 'title',
        help = 'Track title. This can be regex to get the title from the filename.',
    )
    
    tag.add_argument(
        '--track', '-tr',
        dest = 'track',
        help = 'Track number. This can be regex to get the track from the filename.',
    )
    
    tag.add_argument(
        '--band', '-b',
        dest = 'band',
        help = 'Album artist / band',
    )

    tag.add_argument(
        '--album', '-al',
        dest = 'album',
        help = 'Album title',
    )
    
    tag.add_argument(
        '--publisher', '-p',
        dest = 'publisher',
        help = 'Publisher',
    )
    
    tag.add_argument(
        '--genre', '-g',
        dest = 'genre',
        help = 'Genre(s)',
        nargs = '*',
    )
    
    tag.add_argument(
        '--disc', '-d',
        dest = 'disc',
        help = 'Disc number. This can be regex to get the disc from the filename.',
    )
    
    tag.add_argument(
        '--cover', '-c',
        dest = 'cover',
        help = 'Cover art image.',
    )
    
    tag.add_argument(
        '--clear',
        dest = 'clear',
        help = 'Clear metadata before writing',
        action = 'store_true',
    )
    
    tag.add_argument(
        '--spreadsheet', '-s',
        dest = 'spreadsheet',
        help = 'Add a metadata spreadsheet. This csv will have a header, and it will match the first column then add the specified metadata tags.',
    )
    
    create = subparsers.add_parser(
        'create',
        help = 'Create and loop audio files in a soundtrack. More information can be found at https://github.com/ego-lay-atman-bay/python-soundtrack-creator#create',
    )
    
    create.add_argument(
        'input',
        help = 'configuration json path',
    )
    
    if len(sys.argv[1:]) < 1:
        arg_parser.print_help()
        sys.exit()
    
    args = arg_parser.parse_args()
    
    setup_logger(args.log_level)

    if args.command == 'tag':
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
    elif args.command == 'create':
        maker = SoundtrackMaker(args.input)
        maker.create_soundtrack()

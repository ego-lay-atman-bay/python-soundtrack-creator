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
    
    create.add_argument(
        '--dry-run', '-d',
        help = 'print filenames',
        action = 'store_true',
        dest = 'dry_run',
    )
    
    create.add_argument(
        '--tracks', '-t',
        dest = 'tracks',
        help = 'tracks to build',
        nargs = '+',
        type = str,
    )
    
    create.add_argument(
        '--album', '-a',
        dest = 'albums',
        help = 'albums to build',
        nargs = '+',
        type = str,
    )
    
    # dump
    dump = subparsers.add_parser(
        'dump',
        help = 'dump metadata from files in folder',
    )
    
    dump.add_argument(
        'folder',
        help = 'folder to grab metadata from',
    )
    
    dump.add_argument(
        'output',
        help = 'output csv file',
        default = 'metadata.csv',
    )
    
    dump.add_argument(
        '-ho', '--header-order',
        dest = 'order',
        nargs = '+',
        help = 'header order, such as "title" "artist"',
    )
    
    dump.add_argument(
        '-e', '--exclude-unknown',
        dest = 'exclude',
        action = 'store_false',
        help = "exclude tag that aren't in '--header-order'",
    )
    
    dump.add_argument(
        '-a', '--align',
        dest = 'aligned',
        action = 'store_true',
        help = "align output csv",
    )
    
    if len(sys.argv[1:]) < 1:
        arg_parser.print_help()
        sys.exit()
    
    args = arg_parser.parse_args()
    
    setup_logger(args.log_level)

    if args.command == 'tag':
        try:
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
        except:
            logging.exception('Error during soundtrack tagging')
    elif args.command == 'create':
        print(args)
        
        try:
            maker = SoundtrackMaker(args.input, {
                'title': args.tracks,
                'album': args.albums,
            }, args.dry_run)
            maker.create_soundtrack()
        except:
            logging.exception('Error during soundtrack creation')
    
    elif args.command == 'dump':
        from .dump import dump_metadata
        
        dump_metadata(
            args.folder,
            args.output,
            args.order,
            args.exclude,
            align_csv = args.aligned,
        )


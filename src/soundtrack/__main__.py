import sys
import argparse
import logging
from .soundtrack import Soundtrack

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

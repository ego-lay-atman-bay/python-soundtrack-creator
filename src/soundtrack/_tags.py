import io
import filetype
import mutagen
from mutagen import id3, flac, FileType
import typing
from typing import Literal, Type
from PIL import Image


ID3_FRAMES: dict[str, Type[id3._frames.Frame]] = {
    "AENC": id3.AENC,
    "APIC": id3.APIC,
    "ASPI": id3.ASPI,
    "BUF": id3.BUF,
    "CHAP": id3.CHAP,
    "CNT": id3.CNT,
    "COM": id3.COM,
    "COMM": id3.COMM,
    "COMR": id3.COMR,
    "CRA": id3.CRA,
    "CRM": id3.CRM,
    "CTOC": id3.CTOC,
    "ENCR": id3.ENCR,
    "EQU2": id3.EQU2,
    "ETC": id3.ETC,
    "ETCO": id3.ETCO,
    "GEO": id3.GEO,
    "GEOB": id3.GEOB,
    "GP1": id3.GP1,
    "GRID": id3.GRID,
    "GRP1": id3.GRP1,
    "IPL": id3.IPL,
    "IPLS": id3.IPLS,
    "LINK": id3.LINK,
    "LNK": id3.LNK,
    "MCDI": id3.MCDI,
    "MCI": id3.MCI,
    "MLL": id3.MLL,
    "MLLT": id3.MLLT,
    "MVI": id3.MVI,
    "MVIN": id3.MVIN,
    "MVN": id3.MVN,
    "MVNM": id3.MVNM,
    "OWNE": id3.OWNE,
    "PCNT": id3.PCNT,
    "PCST": id3.PCST,
    "PIC": id3.PIC,
    "POP": id3.POP,
    "POPM": id3.POPM,
    "POSS": id3.POSS,
    "PRIV": id3.PRIV,
    "RBUF": id3.RBUF,
    "REV": id3.REV,
    "RVA": id3.RVA,
    "RVA2": id3.RVA2,
    "RVAD": id3.RVAD,
    "RVRB": id3.RVRB,
    "SEEK": id3.SEEK,
    "SIGN": id3.SIGN,
    "SLT": id3.SLT,
    "STC": id3.STC,
    "SYLT": id3.SYLT,
    "SYTC": id3.SYTC,
    "TAL": id3.TAL,
    "TALB": id3.TALB,
    "TBP": id3.TBP,
    "TBPM": id3.TBPM,
    "TCAT": id3.TCAT,
    "TCM": id3.TCM,
    "TCMP": id3.TCMP,
    "TCO": id3.TCO,
    "TCOM": id3.TCOM,
    "TCON": id3.TCON,
    "TCOP": id3.TCOP,
    "TCP": id3.TCP,
    "TCR": id3.TCR,
    "TDA": id3.TDA,
    "TDAT": id3.TDAT,
    "TDEN": id3.TDEN,
    "TDES": id3.TDES,
    "TDLY": id3.TDLY,
    "TDOR": id3.TDOR,
    "TDRC": id3.TDRC,
    "TDRL": id3.TDRL,
    "TDTG": id3.TDTG,
    "TDY": id3.TDY,
    "TEN": id3.TEN,
    "TENC": id3.TENC,
    "TEXT": id3.TEXT,
    "TFLT": id3.TFLT,
    "TFT": id3.TFT,
    "TGID": id3.TGID,
    "TIM": id3.TIM,
    "TIME": id3.TIME,
    "TIPL": id3.TIPL,
    "TIT1": id3.TIT1,
    "TIT2": id3.TIT2,
    "TIT3": id3.TIT3,
    "TKE": id3.TKE,
    "TKEY": id3.TKEY,
    "TKWD": id3.TKWD,
    "TLA": id3.TLA,
    "TLAN": id3.TLAN,
    "TLE": id3.TLE,
    "TLEN": id3.TLEN,
    "TMCL": id3.TMCL,
    "TMED": id3.TMED,
    "TMOO": id3.TMOO,
    "TMT": id3.TMT,
    "TOA": id3.TOA,
    "TOAL": id3.TOAL,
    "TOF": id3.TOF,
    "TOFN": id3.TOFN,
    "TOL": id3.TOL,
    "TOLY": id3.TOLY,
    "TOPE": id3.TOPE,
    "TOR": id3.TOR,
    "TORY": id3.TORY,
    "TOT": id3.TOT,
    "TOWN": id3.TOWN,
    "TP1": id3.TP1,
    "TP2": id3.TP2,
    "TP3": id3.TP3,
    "TP4": id3.TP4,
    "TPA": id3.TPA,
    "TPB": id3.TPB,
    "TPE1": id3.TPE1,
    "TPE2": id3.TPE2,
    "TPE3": id3.TPE3,
    "TPE4": id3.TPE4,
    "TPOS": id3.TPOS,
    "TPRO": id3.TPRO,
    "TPUB": id3.TPUB,
    "TRC": id3.TRC,
    "TRCK": id3.TRCK,
    "TRD": id3.TRD,
    "TRDA": id3.TRDA,
    "TRK": id3.TRK,
    "TRSN": id3.TRSN,
    "TRSO": id3.TRSO,
    "TS2": id3.TS2,
    "TSA": id3.TSA,
    "TSC": id3.TSC,
    "TSI": id3.TSI,
    "TSIZ": id3.TSIZ,
    "TSO2": id3.TSO2,
    "TSOA": id3.TSOA,
    "TSOC": id3.TSOC,
    "TSOP": id3.TSOP,
    "TSOT": id3.TSOT,
    "TSP": id3.TSP,
    "TSRC": id3.TSRC,
    "TSS": id3.TSS,
    "TSSE": id3.TSSE,
    "TSST": id3.TSST,
    "TST": id3.TST,
    "TT1": id3.TT1,
    "TT2": id3.TT2,
    "TT3": id3.TT3,
    "TXT": id3.TXT,
    "TXX": id3.TXX,
    "TXXX": id3.TXXX,
    "TYE": id3.TYE,
    "TYER": id3.TYER,
    "UFI": id3.UFI,
    "UFID": id3.UFID,
    "ULT": id3.ULT,
    "USER": id3.USER,
    "USLT": id3.USLT,
    "WAF": id3.WAF,
    "WAR": id3.WAR,
    "WAS": id3.WAS,
    "WCM": id3.WCM,
    "WCOM": id3.WCOM,
    "WCOP": id3.WCOP,
    "WCP": id3.WCP,
    "WFED": id3.WFED,
    "WOAF": id3.WOAF,
    "WOAR": id3.WOAR,
    "WOAS": id3.WOAS,
    "WORS": id3.WORS,
    "WPAY": id3.WPAY,
    "WPB": id3.WPB,
    "WPUB": id3.WPUB,
    "WXX": id3.WXX,
    "WXXX": id3.WXXX,
}

TAGS: list[
    dict[
        Literal[
            "name",
            "id3",
            "flac",
        ],
        list[str]
        | str
        | dict[
            Literal[
                "id",
                "values",
                "default",
            ],
            str | list[str],
        ],
    ]
] = [
    {
        "name": ["picture", "cover", "artwork"],
        "id3": {
            "id": "APIC",
            "values": ["encoding", "mime", "type", "desc", "data"],
            "default": "data",
        },
        "flac": None,
    },
    {"name": ["comment"], "id3": "COMM", "flac": "comment"},
    {"name": ["grouping", "contentgroup"], "id3": "TIT1", "flac": "contentgroup"},
    {"name": ["arranger", "involvedpeople",], "id3": "TIPL", "flac": "arranger"},
    {"name": ["musiccdidentifier"], "id3": "MCDI", "flac": "musiccdidentifier"},
    {"name": ["movement", "movementnumber"], "id3": "MVIN", "flac": "movement"},
    {"name": ["movementname"], "id3": "MVNM", "flac": "movementname"},
    {"name": ["movementtotal"], "id3": "MVNM", "flac": "movementtotal"},
    {"name": ["ownership"], "id3": "OWNE", "flac": "ownership"},
    {
        "name": ["playcounter"],
        "id3": {"id": "PCNT", "values": ["count"], "default": "count"},
        "flac": "playcounter",
    },
    {"name": ["podcast?", "podcast"], "id3": "PCST", "flac": "podcast"},
    {
        "name": ["popularimeter"],
        "id3": {
            "id": "POPM",
            "values": ["email", "rating", "count"],
            "default": "rating",
        },
        "flac": "rating:{email}",
    },
    {"name": ["private"], "id3": "PRIV", "flac": "private"},
    {"name": ["album"], "id3": "TALB", "flac": "album"},
    {"name": ["bpm", "beatsperminute"], "id3": "TBPM", "flac": "bpm"},
    {"name": ["podcastcategory"], "id3": "TCAT", "flac": "podcastcategory"},
    {"name": ["compilation"], "id3": "TCMP", "flac": "compilation"},
    {"name": ["composer"], "id3": "TCOM", "flac": "composer"},
    {
        "name": ["genres", "genre"],
        "id3": {"id": "TCON", "values": ["text", "genres"], "default": "genres"},
        "flac": "genre",
    },
    {"name": ["copyright"], "id3": "TCOP", "flac": "copyright"},
    {"name": ["date"], "id3": "TDAT", "flac": "date"},
    {"name": ["year"], "id3": "TYER", "flac": "year"},
    {"name": ["podcastdescription"], "id3": "TDES", "flac": "podcastdescription"},
    {"name": ["playlistdelay"], "id3": "TDLY", "flac": "playlistdelay"},
    {"name": ["encodedby"], "id3": "TENC", "flac": "encodedby"},
    {"name": ["lyricist"], "id3": "TEXT", "flac": "lyricist"},
    {"name": ["filetype"], "id3": "TFLT", "flac": "filetype"},
    {"name": ["podcastid"], "id3": "TGID", "flac": "podcastid"},
    {"name": ["time", "releasetime"], "id3": "TIME", "flac": "releasetime"},
    {"name": ["title"], "id3": "TIT2", "flac": "title"},
    {"name": ["subtitle"], "id3": "TIT3", "flac": "subtitle"},
    {"name": ["initialkey"], "id3": "TKEY", "flac": "key"},
    {"name": ["podcastkeywords"], "id3": "TKWD", "flac": "podcastkeywords"},
    {"name": ["language"], "id3": "TLAN", "flac": "language"},
    {"name": ["length"], "id3": "TLEN", "flac": "length"},
    {"name": ["media"], "id3": "TMED", "flac": "media"},
    {"name": ["originalalbum"], "id3": "TOAL", "flac": "originalalbum"},
    {"name": ["origalbum"], "id3": "TOAL", "flac": "origalbum"},
    {"name": ["originalfilename"], "id3": "TOFN", "flac": "originalfilename"},
    {"name": ["originallyricist"], "id3": "TOLY", "flac": "originallyricist"},
    {"name": ["originalartist"], "id3": "TOPE", "flac": "originalartist"},
    {"name": ["origartist"], "id3": "TOPE", "flac": "origartist"},
    {"name": ["originalreleaseyear"], "id3": "TDOR", "flac": "originaldate"},
    {"name": ["fileowner"], "id3": "TOWN", "flac": "fileowner"},
    {"name": ["artist"], "id3": "TPE1", "flac": "artist"},
    {"name": ["band", "albumartist"], "id3": "TPE2", "flac": "albumartist"},
    {"name": ["conductor"], "id3": "TPE3", "flac": "conductor"},
    {"name": ["interpretedby", "remixer"], "id3": "TPE4", "flac": "REMIXER"},
    {
        "name": ["disc", "disk", "cd", "discnumber", "disknumber", "partofset"],
        "id3": "TPOS",
        "flac": "discnumber",
    },
    {"name": ["publisher", "organization"], "id3": "TPUB", "flac": "organization"},
    {"name": ["track", "tracknumber"], "id3": "TRCK", "flac": "tracknumber"},
    {"name": ["recordingdates"], "id3": "TRDA", "flac": "date"},
    {"name": ["recordingtime"], "id3": "TDRC", "flac": "time"},
    {"name": ["size"], "id3": "TSIZ", "flac": "size"},
    {"name": ["isrc"], "id3": "TSRC", "flac": "isrc"},
    {
        "name": ["encodersettings"],
        "id3": "TSSE",
        "flac": "encodersettings",
    },
    {"name": ["termsofuse"], "id3": "USER", "flac": "termsofuse"},
    {"name": ["commercialurl"], "id3": "WCOM", "flac": "commercialurl"},
    {"name": ["copyrighturl", "license"], "id3": "WCOP", "flac": "license"},
    {"name": ["podcasturl"], "id3": "WFED", "flac": "podcasturl"},
    {"name": ["fileurl"], "id3": "WOAF", "flac": "fileurl"},
    {"name": ["artisturl"], "id3": "WOAR", "flac": "website"},
    {"name": ["sourceurl"], "id3": "WOAS", "flac": "sourceurl"},
    {
        "name": ["internetradiostationurl"],
        "id3": "WORS",
        "flac": "internetradiostationurl",
    },
    {"name": ["paymenturl"], "id3": "WPAY", "flac": "paymenturl"},
    {"name": ["publisherurl"], "id3": "WPUB", "flac": "publisherurl"},
    {"name": ["userdefinedurl"], "id3": "WXXX", "flac": "userdefinedurl"},
    {
        "name": ["discs", "disks", "totaldiscs", "totaldisks"],
        "id3": "TXXX:TOTALDISCS",
        "flac": "totaldiscs",
    },
    {
        "name": ["tracks", "totaltracks"],
        "id3": "TXXX:TOTALTRACKS",
        "flac": "totaltracks",
    },
    {
        "name": ["accurateripdiscid"],
        "id3": "TXXX:ACCURATERIPDISCID",
        "flac": "accurateripdiscid",
    },
    {"name": ["source"], "id3": "WOAS", "flac": "source"},
    {"name": ["encodedby"], "id3": "TENC", "flac": "encoded by"},
    {"name": ["encoder"], "id3": "TENC", "flac": "encoder"},
    {
        "name": ["lyrics", "syncedlyrics", "synlyrics"],
        "id3": "SYLT",
        "flac": "lyrics",
    },
    {
        "name": ["unsyncedlyrics"],
        "id3": "USLT",
        "flac": "unsyncedlyrics",
    },
    {"name": ["tempo"], "id3": "TBPM", "flac": "tempo"},
    {"name": ["mood"], "id3": "TMOO", "flac": "mood"},
    {"name": ["occasion"], "id3": "TXXX:OCCASION", "flac": "occasion"},
    {"name": ["keywords"], "id3": "TKWD", "flac": "keywords"},
    {"name": ["tracktotal"], "id3": "TXXX:TRACKTOTAL", "flac": "tracktotal"},
    {
        "name": ["accurateripresult"],
        "id3": "TXXX:ACCURATERIPRESULT",
        "flac": "accurateripresult",
    },
    {
        "name": ["albumartistsortorder", "albumartistsort"],
        "id3": "TSO2",
        "flac": "albumartistsort",
    },
    {"name": ["albumsort"], "id3": "TSOA", "flac": "albumsort"},
    {
        "name": ["composersortorder", "composersort"],
        "id3": "TSOC",
        "flac": "composersort",
    },
    {"name": ["encodingtime"], "id3": "TDEN", "flac": "encodingtime"},
    {"name": ["involvedpeoplelist"], "id3": "TIPL", "flac": "involvedpeoplelist"},
    {"name": ["location"], "id3": "TXXX:LOCATION", "flac": "location"},
    {"name": ["sourcemedium"], "id3": "TXXX:SOURCEMEDIUM", "flac": "sourcemedium"},
    {
        "name": ["musiciancreditslist"],
        "id3": "TXXX:MUSICIANCREDITSLIST",
        "flac": "musiciancreditslist",
    },
    {"name": ["userdefinedtext"], "id3": "TXXX", "flac": "comment"},
    {
        "name": ["internetradiostationname", "netradiostation"],
        "id3": "TRSN",
        "flac": "netradiostation",
    },
    {
        "name": ["internetradiostationowner", "netradioowner"],
        "id3": "TRSO",
        "flac": "netradioowner",
    },
    {"name": ["subtitle", "setsubtitle"], "id3": "TSST", "flac": "setsubtitle"},
    {"name": ["titlesort"], "id3": "TSOT", "flac": "titlesort"},
    {"name": ["chapter"], "id3": "CHAP", "flac": "chapter"},
    {"name": ["toc", "tableofcontents"], "id3": "CTOC", "flac": "tableofcontents"},
]

__all__ = [
    "TAGS",
    "ID3_FRAMES",
    "get_tag",
    "set_tag",
    "remove_tag",
    "set_picture",
    "get_tag_name",
    "get_tag_id",
    "get_tag_info",
]


def get_tag(audio: FileType, tag: str):
    if not isinstance(audio, FileType):
        raise TypeError("not mutagen audio object")

    if audio.tags == None:
        return

    if isinstance(audio.tags, id3.ID3):
        return _get_id3_tag(audio.tags, tag)
    elif isinstance(audio.tags, flac.VCFLACDict):
        return _get_flac_tag(audio.tags, tag)

    raise NotImplementedError("audio type not supported")


def set_tag(audio: FileType, tag: str, value: str, **kwargs):
    if not isinstance(audio, FileType):
        raise TypeError("not mutagen audio object")

    if audio.tags == None:
        return

    if isinstance(audio.tags, id3.ID3):
        return _set_id3_tag(audio.tags, tag, value=value, **kwargs)
    elif isinstance(audio.tags, flac.VCFLACDict):
        return _set_flac_tag(audio.tags, tag, value=value)

    raise NotImplementedError("audio type not supported")

def set_picture(audio: FileType, image: str | bytes | io.BytesIO | Image.Image):
    if not isinstance(audio, FileType):
        raise TypeError("not mutagen audio object")

    if audio.tags == None:
        return
    
    if isinstance(image, str):
        picture = Image.open(image)
    elif isinstance(image, bytes):
        data = io.BytesIO(image)
        data.seek(0)
        picture = Image.open(data)
    elif isinstance(image, Image.Image):
        picture = image.copy()
    elif hasattr(image, 'read') and hasattr(image, 'seek') and hasattr(image, 'call'):
        image.seek(0)
        picture = Image.open(image)
    elif image == None:
        picture = image
    else:
        raise TypeError('not a valid image')
    
    if isinstance(audio.tags, id3.ID3):
        return _set_id3_picture(audio.tags, picture)
    elif isinstance(audio.tags, flac.VCFLACDict):
        return _set_flac_picture(audio, picture)

    raise NotImplementedError("audio type not supported")

def _set_id3_picture(tags: id3.ID3, image: Image.Image):
    _remove_id3_tag(tags, 'picture')
    
    if image == None:
        return
    
    picture = io.BytesIO()
    image.save(picture, format = 'JPEG')
    
    picture.seek(0)
    
    data = picture.getvalue()
    mime = filetype.guess(data)
    
    _set_id3_tag(
        tags,
        'picture',
        encoding = 3,  # 3 is for utf-8
        mime = mime,  # image/jpeg or image/png
        type = id3.PictureType.COVER_FRONT,  # 3 is for the cover image
        desc = "Cover",
        data = data,
    )

def _set_flac_picture(audio: FileType, image: Image.Image):
    audio.clear_pictures()
    
    if image == None:
        return
    
    picture = io.BytesIO()
    image.save(image, format = 'JPEG')
    
    picture.seek(0)
    
    data = picture.getvalue()
    mime = filetype.guess(data)

    picture = flac.Picture()
    picture.data = data
    picture.type = id3.PictureType.COVER_FRONT
    picture.mime = mime
    picture.width = image.width
    picture.height = image.height

    audio.add_picture(picture)

def remove_tag(audio: FileType, tag: str):
    if not isinstance(audio, FileType):
        raise TypeError("not mutagen audio object")

    if audio.tags == None:
        return

    if isinstance(audio.tags, id3.ID3):
        return _remove_id3_tag(audio.tags, tag)
    elif isinstance(audio.tags, flac.VCFLACDict):
        return _remove_flac_tag(audio.tags, tag)

    raise NotImplementedError("audio type not supported")


def get_tag_info(type: Literal["id3", "flac"], tag: str):
    split = tag.split(":")
    desc = split[1] if len(split) > 1 else ""

    tag = split[0]

    result = ""

    for tag_info in TAGS:
        if tag.lower() in tag_info["name"]:
            return tag_info[type]
        tag_id = tag_info[type]
        if isinstance(tag_id, dict):
            tag_id = tag_id["id"]

        if tag_id == None:
            continue

        split = tag_id.split(":")

        tag_id = split[0]
        tag_desc = split[1] if len(split) > 1 else ""

        if tag.lower() == tag_id.lower():
            if tag_desc.lower() == desc.lower():
                return tag_info[type]

            result = tag_info[type]

    return result if result else tag


def get_tag_id(type: Literal["id3", "flac"], tag: str):
    id = get_tag_info(type, tag)
    if isinstance(id, dict):
        return id["id"]
    return id

def get_tag_name(tag: str):
    split = tag.split(':')
    tag = split[0]
    desc = split[1] if len(split) > 1 else ''
    
    for tag_info in TAGS:
        if tag.lower() in tag_info["name"]:
            return tag_info["name"][0]
        
        result = ''
        
        for type in ['id3', 'flac']:
            tag_name = tag_info[type]
            
            if isinstance(tag_name, dict):
                tag_name = tag_name['id']
                
            if tag_name == None:
                continue
                
            split = tag_name.split(':')
            tag_name = split[0]
            tag_desc = split[1] if len(split) > 1 else ''
        
            if tag.lower() == tag_name.lower():
                if desc == tag_desc:
                    return tag_info["name"][0]

                result = tag_info["name"][0]
        
    return result if result else tag

def _get_id3_tag(tags: id3.ID3, tag: str):
    id = get_tag_info("id3", tag)
    prop = 'text'
    if isinstance(id, dict):
        if 'default' in id:
            prop = id['default']
        id = id['id']

    value = None

    if id.split(':')[0] in ID3_FRAMES:
        values = tags.getall(id)
        if len(values) > 0:
            value = values[0]
    
    if isinstance(value, id3._frames.Frame):
        value = getattr(value, prop)
        if prop == 'text':
            value = str(value[0])

    return value


def _get_flac_tag(tags: flac.VCFLACDict, tag: str):
    id = get_tag_id("flac", tag)

    return tags.get(id, [None])[0]


def _set_id3_tag(tags: id3.ID3, tag: str, value: str = None, **kwargs):
    info = get_tag_info("id3", tag)
    id = info
    genres = False
    if isinstance(info, dict):
        id = info["id"]

        if value:
            if "default" in info:
                if info["default"] not in kwargs:
                    kwargs[info["default"]] = value
                    if info['default'] == 'genres':
                        genres = True
            else:
                if "text" not in kwargs:
                    kwargs["text"] = value

    else:
        if value and "text" not in kwargs:
            kwargs["text"] = value

    if id not in ID3_FRAMES:
        id = f"TXXX:{id}"

    split = id.split(":")
    id = split[0]
    desc = split[1] if len(split) > 1 else None

    if "desc" in kwargs:
        desc = f'{desc}:{kwargs["desc"]}'

    kwargs["desc"] = desc

    frame = ID3_FRAMES[id]
    
    tag_frame = frame(**kwargs)
    
    if genres:
        if hasattr(tag_frame, 'genres'):
            tag_frame.genres = value if isinstance(value, list) else [value]

    tags.add(tag_frame)


def _set_flac_tag(tags: flac.VCFLACDict, tag: str, value: str):
    id = get_tag_id("flac", id)

    tags[id] = value


def _remove_id3_tag(tags: id3.ID3, tag: str):
    id = get_tag_id('id3', tag)

    tags.delall(id)


def _remove_flac_tag(tags: flac.VCFLACDict, tag: str):
    id = get_tag_id('flac', tag)

    del tags[id]

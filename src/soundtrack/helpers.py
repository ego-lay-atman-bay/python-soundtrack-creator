import os
from copy import deepcopy
from typing import Any, IO
import io

import charset_normalizer
import json5


def is_int(value: Any) -> bool:
    if isinstance(value, float):
        return False
    try:
        int(value)
        return True
    except:
        return False

def is_float(value: Any) -> bool:
    try:
        float(value)
        return True
    except:
        return False

def str_type(string: str):
    if is_int(string):
        return 'int'
    elif is_float(string):
        return 'float'
    else:
        return 'str'

def str_to_num(string: str):
    if is_int(string):
        return int(string)
    elif is_float(string):
        return float(string)
    else:
        return string

def read_text_or_file(text_or_file: str, base_path):
    if os.path.isfile(path := os.path.join(base_path, text_or_file)):
        with open(path, 'r') as file:
            return file.read()
    else:
        return text_or_file
    
def read_json_file(file) -> dict:
    try:
        if file == None:
            return {}
        elif (isinstance(file, dict)):
            return deepcopy(file)
        elif (isinstance(file, str)):
            if os.path.isfile(file):
                json_file = charset_normalizer.from_path(file).best()
                return json5.loads(json_file.output().decode())
            else:
                return json5.loads(file)
        elif (hasattr(file, 'read')):
            return json5.load(file)
        else:
            raise TypeError('json file must be dict, file path, or file')

    except Exception as e:
        e.add_note(file)
        raise e

def is_text_file(file: IO):
    return isinstance(file, io.TextIOBase)


def is_binary_file(file: IO):
    return isinstance(file, (io.RawIOBase, io.BufferedIOBase))

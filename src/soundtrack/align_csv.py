import csv
import io
import os
import sys
from contextlib import nullcontext
from itertools import zip_longest
from typing import Any, Literal, IO

import charset_normalizer

from .helpers import is_binary_file, is_text_file


def isnumeric(value: str):
    try:
        float(value)
        return True
    except:
        return False

def align(table: list[list[str]], dialect: csv.Dialect = csv.excel):
    columns = []
    
    for column in zip_longest(*table, fillvalue = ''):
        max_length = max([len(cell) for cell in column]) + 1

        columns.append([f'{cell:{['<', '>'][isnumeric(cell)]}{max_length}}' for cell in column])
    
    return list(zip_longest(*columns, fillvalue = ''))

def escape_table(table: list[list[str]], dialect: csv.Dialect = csv.excel):
    return [[escape_cell(cell, dialect) for cell in row] for row in table]

def escape_cell(cell: str, dialect: csv.Dialect = csv.excel):
    quote = False | dialect.quoting == csv.QUOTE_ALL
    
    if dialect.quoting == csv.QUOTE_NONNUMERIC:
        if not isnumeric(cell):
            quote = True
    elif dialect.quoting == csv.QUOTE_STRINGS:
        if not isnumeric(cell):
            quote = True
        elif cell == None:
            quote = False
            cell = ""
    elif dialect.quoting == csv.QUOTE_NOTNULL:
        if cell == None:
            quote = False
            cell = ""
        else:
            quote = True
    if cell is None:
        cell = ''
    cell = str(cell)
    if dialect.escapechar and dialect.escapechar in cell:
        cell = cell.replace(dialect.escapechar, dialect.escapechar + dialect.delimiter)
    
    if dialect.delimiter in cell:
        if dialect.quoting == csv.QUOTE_NONE:
            if not dialect.escapechar:
                raise csv.Error('need to escape, but no escapechar set')

            cell = cell.replace(dialect.delimiter, dialect.escapechar + dialect.delimiter)
        else:
            quote = True
    
    if dialect.quotechar in cell:
        if dialect.doublequote:
            cell = cell.replace(dialect.quotechar, dialect.quotechar + dialect.quotechar)
            quote = True
        else:
            if not dialect.escapechar:
                raise csv.Error('need to escape, but no escapechar set')
            
            cell = cell.replace(dialect.quotechar, dialect.escapechar + dialect.quotechar)

    if dialect.lineterminator in cell:
        if dialect.quoting == csv.QUOTE_NONE:
            if not dialect.escapechar:
                raise csv.Error('need to escape, but no escapechar set')

            cell = cell.replace(dialect.lineterminator, dialect.escapechar + dialect.lineterminator)
        else:
            quote = True
    
    if quote:
        cell = dialect.quotechar + cell + dialect.quotechar
        
    return cell
    

def minify(table: list[list[str]]):
    return [[str(cell).strip() if cell != None else cell for cell in row] for row in table]

def aligned_csv(table: list[list[str]], **kwargs):
    writer = csv.writer(io.StringIO(), **kwargs)
    dialect = writer.dialect
    
    table = align(escape_table(minify(table)))
    
    rows = []
    
    for row in table:
        rows.append(dialect.delimiter.join([str(cell) for cell in row]).rstrip())

    return '\n'.join(rows)

def read_csv(filename: str):
    table = []
    
    encoding = charset_normalizer.from_path(filename).best().encoding
    
    with open(filename, 'r', newline = '', encoding = encoding) as file:
        table = list(csv.reader(file))
    
    return table, encoding

def write_csv(
    file: str | IO,
    table: list[list],
    encoding: str | None = None,
    **kwargs
):
    is_binary: bool = False
    
    if isinstance(file, str):
        context_manager = open(file, 'r', newline = '', encoding = encoding)
    elif is_text_file(file):
        context_manager = nullcontext(file)
    elif is_binary_file(file):
        context_manager = nullcontext(file)
        is_binary = True
    else:
        raise TypeError('cannot open file')
    
    with context_manager as file:
        aligned = aligned_csv(table, **kwargs)
        if is_binary:
            aligned = aligned.encode(encoding)
        file.write(aligned)

def write_dict_csv(
    file: str | IO,
    table: list[dict[str, Any]],
    fieldnames: list[str],
    restval: Any | None = "",
    extrasaction: Literal['raise', 'ignore'] = "raise",
    write_header: bool = True,
    **kwargs
):
    fieldnames = list(fieldnames)
    fieldnames_set = set(fieldnames)
    new_table = []
    if write_header:
        new_table.append(fieldnames)
    
    for row_dict in table:
        if extrasaction == 'raise':
            unknown = set(row_dict.keys()) - fieldnames_set
            if len(unknown):
                raise ValueError(f"dict contains fields not in fieldnames: {', '.join([repr(key) for key in unknown])}")

        new_table.append([row_dict.get(key, restval) for key in fieldnames])
    
    write_csv(
        file,
        new_table,
        **kwargs,
    )
    

if __name__ == "__main__":
    args = sys.argv[1::]

    if len(args) < 1:
        print("usage: align_csv.py <input> <output>")
        exit()
    
    input = args[0]
    output = args[0]
    if len(args) > 1:
        output = args[1]
    
    table, encoding = read_csv(input)
    
    write_csv(table, output, encoding)

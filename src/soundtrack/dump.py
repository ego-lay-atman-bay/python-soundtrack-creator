import csv
import os
import sys

import audioman

from .align_csv import write_dict_csv

def dump_metadata(
    dir: str,
    output: str,
    order: list[str] | None = None,
    include_unknown: bool = True,
    align_csv: bool = True,
):
    table = []
    columns = set()
    
    
    for root, dirs, files in os.walk(dir):
        for filename in files:
            tags = audioman.AudioTags(os.path.join(root, filename))
            columns.update(tags.keys())
            table.append(dict(tags))
    
    header = list(columns)
    if order:
        header = [key for key in order if key in columns]
        if include_unknown:
            unknown = set(columns) - set(order)
            header.extend(unknown)
    
    # return header, table
    
    with open(output, 'w', newline = '', encoding = 'utf-8') as file:
        if align_csv:
            write_dict_csv(
                file,
                table,
                header,
                extrasaction = 'ignore',
                write_header = True,
            )
        else:
            writer = csv.DictWriter(file, header)

            writer.writeheader()
            writer.writerows(table)
        
        

if __name__ == "__main__":
    dump_metadata(sys.argv[1], sys.argv[2])

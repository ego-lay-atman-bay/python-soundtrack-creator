class SafeFormatDict(dict):
    def __missing__(self, key):
        return f'{{{key}}}'

def format(string: str, **values: dict[str,str]):
    for key in values:
        try:
            values[key] = int(values[key])
        except:
            try:
                values[key] = float(values[key])
            except:
                pass
    return string.format_map(SafeFormatDict(values))

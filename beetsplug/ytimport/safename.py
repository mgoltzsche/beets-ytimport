import re
import unicodedata

_name_regex = re.compile(r'[^-a-zA-Z0-9_:\(\)\[\]&]+')

def safe_name(name):
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = name.replace('"', '_')
    name = name.replace("'", ' ')
    name = _name_regex.sub(' ', name)
    name = name.replace(':', '-')
    if len(name) > 100:
        name = name[:100]
    return name.strip(' ')

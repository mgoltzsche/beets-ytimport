from slugify import slugify

def safe_name(name):
    name = slugify(name, lowercase=False, separator=' ', replacements=(('"', '_',),("'", ' '),), regex_pattern=r'[^-a-zA-Z0-9_:\(\)\[\]&]+')
    name = name.replace(':', '-')
    return name

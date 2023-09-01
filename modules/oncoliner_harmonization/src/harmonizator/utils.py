import re

def cleanup_text(txt: str):
    special_chars_regex = r'[^a-zA-Z0-9]'
    return re.sub(special_chars_regex, '_', txt)

import os
import re
import json

from collections.abc import MutableMapping
from collections import OrderedDict
from functools import cmp_to_key

config = None


def clean_string(string: str):
    special_chars_regex = r'[^a-zA-Z0-9]'
    return re.sub(special_chars_regex, '_', string)


def path_to_pipeline_name(path: str):
    return os.path.split(path)[-1]


def flatten_dict(dict_, key_limit=None):
    items = []

    if key_limit and key_limit in dict_:
        items.append(dict_)
    else:
        for v in dict_.values():
            if isinstance(v, MutableMapping):
                items.extend(flatten_dict(v, key_limit))
            else:
                items.append(v)

    return items


def flatten_dict_keys(dict_, value_key, depth=0, key=None, concat_key=""):
    items = []

    if not concat_key:
        concat_key = key;
    elif key:
        concat_key = concat_key + " ; " + key

    currDict = {'key': key, 'depth': depth, 'concat_key': concat_key}

    if value_key in dict_:
        currDict[value_key] = dict_[value_key]
        items.append(currDict)
    else:
        if '_all_' in dict_:
            items.append({'key': key, 'depth': depth, 'concat_key': concat_key, value_key: dict_['_all_'][value_key]})
        for k in dict_:
            v = dict_[k]
            if isinstance(v, MutableMapping) and k != '_all_':
                items.extend(flatten_dict_keys(v, value_key, depth + 1, k, concat_key))

    return items


def get_conf():
    global config
    if not config:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html_templates', 'conf.json')) as f:
            config = json.load(f)
    return config


def make_comparator(less_than):
    def compare(x, y):
        if less_than(x, y):
            return -1
        elif less_than(y, x):
            return 1
        else:
            return 0
    return compare


def to_sorted_dict(src_dict, comparator):
    sorted_keys = sorted(src_dict.keys(), key=cmp_to_key(make_comparator(comparator)), reverse=False)
    sorted_dict = OrderedDict()

    for key in sorted_keys:
        sorted_dict[key] = src_dict[key]

    return sorted_dict

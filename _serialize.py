# -*- encoding: utf-8 -*-

import calendar
import cPickle
import datetime
import json
import time


class JsonDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self._object_hook)

    def _object_hook(self, obj):
        # Epoch --> datetime.datetime
        if 'type' in obj and obj['type'] == 'epoch':
            # First 6 fields of time_struct for datetime() constructor
            return datetime.datetime(*time.gmtime(obj['value'])[:6])
        return obj


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        # datetime.datetime --> Epoch
        if hasattr(obj, 'timetuple'):
            return {'type': 'epoch', 'value': calendar.timegm(obj.timetuple())}
        return json.JSONEncoder.default(self, obj)


def get_pickle_path(fname):
    from os import path
    return path.join('pickles', fname)


def pickle_file(obj, fname, protocol=-1):
    with open(get_pickle_path(fname), 'wb') as f:
        return cPickle.dump(obj, f, protocol=protocol)


def unpickle_file(fname):
    with open(get_pickle_path(fname), 'rb') as f:
        return cPickle.load(f)

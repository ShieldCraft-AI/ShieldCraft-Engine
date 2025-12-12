from collections.abc import MutableMapping
import json
from pathlib import Path

class Recorder:
    def __init__(self):
        self.paths = set()
        self.prefix = ""

    def child(self, key):
        r = Recorder()
        r.paths = self.paths
        r.prefix = (self.prefix + "/" + key).lstrip("/")
        return r

    def record(self, key):
        full = (self.prefix + "/" + key).lstrip("/")
        self.paths.add(full)

    def dump(self, out_path):
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sorted(self.paths), f, indent=2)

class TrackingDict(MutableMapping):
    def __init__(self, data, recorder):
        self._data = data
        self._recorder = recorder

    def _wrap(self, key, value):
        if isinstance(value, dict):
            return TrackingDict(value, self._recorder.child(key))
        return value

    def __getitem__(self, key):
        self._recorder.record(str(key))
        return self._wrap(key, self._data[key])

    def get(self, key, default=None):
        self._recorder.record(str(key))
        return self._wrap(key, self._data.get(key, default))

    def __iter__(self):
        for k in self._data:
            self._recorder.record(str(k))
            yield k

    def __len__(self):
        return len(self._data)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        self._recorder.record(str(key))
        return key in self._data

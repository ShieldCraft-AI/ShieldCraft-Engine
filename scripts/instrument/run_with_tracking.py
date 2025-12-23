from scripts.instrument.raw_tracker import Recorder, TrackingDict
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


SPEC = "spec/se_dsl_v1.spec.json"
OUT = "artifacts/dsl_field_usage.json"


def load_raw(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    raw = load_raw(SPEC)
    recorder = Recorder()
    tracked = TrackingDict(raw, recorder)

    # Minimal forced traversal: enumerate all keys deeply
    def walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k in obj:
                obj[k]  # triggers recorder
                walk(obj[k], prefix + "/" + k)

    walk(tracked)

    recorder.dump(OUT)
    print("tracking_complete")


if __name__ == "__main__":
    main()

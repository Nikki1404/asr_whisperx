import json
from pathlib import Path

def save_json(data, path):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def save_txt(lines, path):
    Path(path).write_text("\n".join(lines), encoding="utf-8")

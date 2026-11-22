"""スクリプト共通：設定とデータの読み込み。"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
EXAMPLE = ROOT / "config.example"
MESSAGES = ROOT / "data" / "messages.jsonl"
MATCHES = ROOT / "data" / "matches"
RESOLVED = ("good", "neutral", "bad", "no_reply")
RESULTS = RESOLVED + ("pending",)


def load_settings():
    """config/settings.json を読む。無ければ雛形を使う。"""
    for base in (CONFIG, EXAMPLE):
        p = base / "settings.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{p.relative_to(ROOT)} が壊れてる: {e}")
    return {"stages": [], "tactics": {}, "min_samples": 5}


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.split("#")[0].strip()
    return out


def load_messages(since=None):
    rows = []
    if not MESSAGES.exists():
        return rows
    for n, line in enumerate(MESSAGES.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"messages.jsonl {n}行目が壊れてる: {e}")
        if since and row.get("date", "") < since:
            continue
        rows.append(row)
    return rows


def load_matches():
    out = []
    if not MATCHES.exists():
        return out
    for p in sorted(MATCHES.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        meta = front_matter(text)
        meta.setdefault("id", p.stem)
        meta["_text"] = text
        out.append(meta)
    return out

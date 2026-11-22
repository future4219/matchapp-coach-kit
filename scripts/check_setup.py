#!/usr/bin/env python3
"""セットアップが済んでいるか確認する。

使い方: python3 scripts/check_setup.py          # 結果を表示（未完了なら終了コード1）
        python3 scripts/check_setup.py --hook   # SessionStart フック用（常に終了コード0）
"""

import json
import sys

from common import CONFIG, MESSAGES, ROOT, RESULTS, front_matter, load_settings

FILES = ["profile.md", "me.md", "style.md", "settings.json"]


def check():
    problems, todos = [], []
    if not CONFIG.exists():
        return ["config/ がまだ無い（セットアップ前）"], todos
    for name in FILES:
        p = CONFIG / name
        if not p.exists():
            problems.append(f"config/{name} が無い")
            continue
        text = p.read_text(encoding="utf-8")
        n = text.count("TODO")
        if n:
            todos.append(f"config/{name}: TODO {n}か所")
    prof = CONFIG / "profile.md"
    if prof.exists() and front_matter(prof.read_text(encoding="utf-8")).get("setup_done") != "true":
        problems.append("config/profile.md の setup_done が true になっていない")

    settings = load_settings()
    stages, tactics = set(settings.get("stages", [])), set(settings.get("tactics", {}))
    if MESSAGES.exists():
        for n, line in enumerate(MESSAGES.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"data/messages.jsonl {n}行目が壊れてる")
                continue
            if d.get("stage") not in stages:
                todos.append(f"messages.jsonl {n}行目: stage '{d.get('stage')}' が settings.json に無い")
            for t in d.get("tactics", []):
                if t not in tactics:
                    todos.append(f"messages.jsonl {n}行目: tactic '{t}' が settings.json に無い")
            if d.get("result") not in RESULTS:
                problems.append(f"messages.jsonl {n}行目: result '{d.get('result')}' が不正")
    return problems, todos


def main():
    hook = "--hook" in sys.argv
    problems, todos = check()
    if hook:
        if problems:
            print("[matchapp-coach-kit] セットアップが未完了: " + " / ".join(problems)
                  + "。ユーザーの最初の相談に入る前に、matchapp-setup スキルでセットアップを提案すること。")
        elif todos:
            print("[matchapp-coach-kit] セットアップ済み。未記入: " + " / ".join(todos[:5]))
        sys.exit(0)

    if not problems and not todos:
        print("セットアップOK")
    for p in problems:
        print("未完了: " + p)
    for t in todos:
        print("未記入: " + t)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""全員の今の状況を一覧で出す（並行して進めるとき用）。

使い方: python3 scripts/status.py [--all]   # --all で dead も表示

ボール:
  こっち   … 相手の返信が来ていて、こちらが返す番
  相手待ち … こちらが送って返信待ち（pending）
  止まり   … 最後の1通が no_reply
"""

import argparse
import re

from common import load_matches, load_messages


def next_action(text):
    m = re.search(r"## 次の一手\n(.*?)(\n## |\Z)", text, re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = line.strip("- ").strip()
        if line:
            return line
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    last = {}
    for d in load_messages():
        if d["match"] not in last or d["date"] >= last[d["match"]]["date"]:
            last[d["match"]] = d

    rows = []
    for fm in load_matches():
        mid = fm["id"]
        if fm.get("status") == "dead" and not args.all:
            continue
        d = last.get(mid)
        if d is None:
            ball, date = "-", "-"
        elif d.get("result") == "pending":
            ball, date = "相手待ち", d["date"]
        elif d.get("result") == "no_reply":
            ball, date = "止まり", d["date"]
        else:
            ball, date = "こっち", d["date"]
        called = fm.get("called", "")
        if called in ("null", "") or "まだ" in called:
            called = "（名前未）"
        rows.append((ball, date, mid, fm.get("display", ""), called,
                     fm.get("stage", ""), fm.get("status", ""), next_action(fm["_text"])))

    if not rows:
        print("まだ相手が登録されてない（data/matches/ が空）")
        return
    order = {"こっち": 0, "相手待ち": 1, "止まり": 2, "-": 3}
    rows.sort(key=lambda r: (order[r[0]], r[1]))
    print("| ボール | 最終 | id | 表示名 | 呼び方 | 段階 | 状態 | 次の一手 |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")


if __name__ == "__main__":
    main()

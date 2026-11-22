#!/usr/bin/env python3
"""data/ のログを集計して、マークダウンのレポートを標準出力に出す。

使い方: python3 scripts/analyze.py [--since YYYY-MM-DD]
段階と型の一覧・ラベルは config/settings.json から読む。
"""

import argparse
from collections import Counter, defaultdict

from common import RESOLVED, load_matches, load_messages, load_settings


def rate(counter):
    total = sum(counter[r] for r in RESOLVED)
    if total == 0:
        return "-", 0
    return f"{counter['good'] / total:.0%}", total


def table(title, groups, labels, min_samples):
    lines = [f"## {title}", "", "| 型 | 結果が出た数 | good率 | good | neutral | bad | 無視 | 保留 |",
             "|---|---|---|---|---|---|---|---|"]
    order = sorted(groups.items(), key=lambda kv: -sum(kv[1][r] for r in RESOLVED))
    for name, c in order:
        pct, total = rate(c)
        flag = "" if total >= min_samples else " ※少"
        label = f"{name}（{labels[name]}）" if name in labels else f"{name}（未登録）"
        lines.append(f"| {label}{flag} | {total} | {pct} | {c['good']} | {c['neutral']} | {c['bad']} | {c['no_reply']} | {c['pending']} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="この日付以降だけ集計 (YYYY-MM-DD)")
    args = ap.parse_args()

    settings = load_settings()
    stages = settings.get("stages", [])
    tactic_labels = settings.get("tactics", {})
    stage_labels = settings.get("stage_labels", {})
    min_samples = settings.get("min_samples", 5)

    msgs = load_messages(args.since)
    matches = load_matches()
    if not msgs:
        print("まだ記録が無い。送ったら「これ送った」で記録していこう。")
        return

    by_tactic, by_stage, overall, delays = defaultdict(Counter), defaultdict(Counter), Counter(), []
    for m in msgs:
        res = m.get("result", "pending")
        overall[res] += 1
        by_stage[m.get("stage", "?")][res] += 1
        for t in m.get("tactics", []):
            by_tactic[t][res] += 1
        if isinstance(m.get("reply_delay_min"), (int, float)):
            delays.append(m["reply_delay_min"])

    pct, total = rate(overall)
    out = [
        "# マチアプ分析レポート",
        "",
        f"- 記録したメッセージ: {len(msgs)}通（結果あり {total}通 / 保留 {overall['pending']}通）",
        f"- 全体のgood率: {pct}",
    ]
    if delays:
        delays.sort()
        out.append(f"- 返信までの時間（中央値）: {delays[len(delays) // 2]}分")
    out.append(f"- ※少 = {min_samples}件未満。傾向として見るだけで、ルール変更の根拠にはしない")
    out.append("")
    out.append(table("型ごとの結果", by_tactic, tactic_labels, min_samples))
    out.append("")
    stage_groups = {s: by_stage[s] for s in stages if s in by_stage}
    stage_groups.update({s: c for s, c in by_stage.items() if s not in stages})
    out.append(table("段階ごとの結果", stage_groups, stage_labels, min_samples))
    out.append("")

    out.append("## 相手ごとの到達段階")
    out.append("")
    funnel = Counter(m.get("stage", "?") for m in matches)
    status = Counter(m.get("status", "?") for m in matches)
    for s in stages:
        reached = sum(1 for m in matches
                      if m.get("stage") in stages and stages.index(m["stage"]) >= stages.index(s))
        out.append(f"- {stage_labels.get(s, s)}: {reached}人（今ここ {funnel.get(s, 0)}人）")
    out.append("- 状態: " + ", ".join(f"{k} {v}人" for k, v in status.items()))
    out.append("")

    misses = [m for m in msgs if m.get("result") in ("bad", "no_reply")]
    if misses:
        out.append("## うまくいかなかったメッセージ")
        out.append("")
        for m in misses[-10:]:
            reply = m.get("reply") or "（返信なし）"
            out.append(f"- [{m.get('match')}/{m.get('stage')}] 「{m.get('text')}」→ {reply}（{', '.join(m.get('tactics', []))}）")
        out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    main()

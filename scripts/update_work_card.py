#!/usr/bin/env python3
"""Regenerate Work cards: bold type, PR stats, latest commit, today's date."""

from __future__ import annotations

import html
import json
import subprocess
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "v3"
W = 2000
LOGIN = "prabhuatbhanzu"
IST = ZoneInfo("Asia/Kolkata")

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"

THEMES = {
    "dark": dict(
        panel="#0E1520",
        panel2="#121A27",
        border="#243041",
        text="#F2F6FC",
        muted="#A8B4C6",
        faint="#7A8AA0",
        accent="#4DA3FF",
        open="#3FB950",
        merged="#A371F7",
        draft="#D29922",
        closed="#F85149",
    ),
    "light": dict(
        panel="#FFFFFF",
        panel2="#EEF3F9",
        border="#D0DAE6",
        text="#0B1220",
        muted="#3D4B5C",
        faint="#5C6B80",
        accent="#1769E0",
        open="#1A7F37",
        merged="#8250DF",
        draft="#9A6700",
        closed="#CF222E",
    ),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def gh_search_count(query: str) -> int:
    q = urllib.parse.quote(query)
    out = subprocess.check_output(
        ["gh", "api", f"search/issues?q={q}&per_page=1"],
        text=True,
    )
    return int(json.loads(out).get("total_count", 0))


def pr_stats() -> dict[str, int]:
    return {
        "open": gh_search_count(f"author:{LOGIN} type:pr is:open draft:false"),
        "draft": gh_search_count(f"author:{LOGIN} type:pr is:open draft:true"),
        "merged": gh_search_count(f"author:{LOGIN} type:pr is:merged"),
        "closed": gh_search_count(f"author:{LOGIN} type:pr is:closed is:unmerged"),
    }


def latest_commit() -> dict:
    sha = git("log", "-1", "--format=%h")
    subject = git("log", "-1", "--format=%s")
    iso = git("log", "-1", "--format=%cI")
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    secs = int((now - dt.astimezone(timezone.utc)).total_seconds())
    if secs < 60:
        rel = "just now"
    elif secs < 3600:
        rel = f"{secs // 60}m ago"
    elif secs < 86400:
        rel = f"{secs // 3600}h ago"
    else:
        rel = f"{secs // 86400}d ago"
    subj = subject.strip()
    if len(subj) > 64:
        subj = subj[:61] + "…"
    return {"sha": sha, "subject": subj, "rel": rel}


def work_svg(p: dict, commit: dict, prs: dict[str, int], today: str) -> str:
    h = 560
    cards = [
        ("Open", prs["open"], p["open"]),
        ("Merged", prs["merged"], p["merged"]),
        ("Drafts", prs["draft"], p["draft"]),
        ("Closed", prs["closed"], p["closed"]),
    ]
    gap = 24
    outer = 56
    usable = W - 2 * outer - 3 * gap
    cw = usable // 4
    cy = 270
    ch = 170

    sha = html.escape(commit["sha"])
    subject = html.escape(commit["subject"])
    rel = html.escape(commit["rel"])
    today_e = html.escape(today)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Work and pull requests" text-rendering="geometricPrecision">',
        f'<rect width="{W}" height="{h}" rx="24" fill="{p["panel"]}" stroke="{p["border"]}"/>',
        f'<text x="56" y="64" fill="{p["text"]}" font-family="{FONT}" font-size="40" font-weight="800">Work</text>',
        f'<text x="{W-56}" y="64" text-anchor="end" fill="{p["accent"]}" font-family="{MONO}" font-size="26" font-weight="800">{today_e}</text>',
        f'<rect x="56" y="82" width="88" height="5" rx="2.5" fill="{p["accent"]}"/>',
        f'<rect x="56" y="110" width="{W-112}" height="64" rx="18" fill="{p["panel2"]}" stroke="{p["border"]}"/>',
        f'<text x="84" y="146" fill="{p["accent"]}" font-family="{MONO}" font-size="24" font-weight="800">latest</text>',
        f'<text x="200" y="146" fill="{p["faint"]}" font-family="{MONO}" font-size="24" font-weight="800">{sha}</text>',
        f'<text x="320" y="146" fill="{p["text"]}" font-family="{FONT}" font-size="26" font-weight="700">{subject}</text>',
        f'<text x="{W-84}" y="146" text-anchor="end" fill="{p["muted"]}" font-family="{FONT}" font-size="24" font-weight="700">{rel}</text>',
        f'<text x="56" y="220" fill="{p["muted"]}" font-family="{FONT}" font-size="26" font-weight="800">Pull requests</text>',
    ]

    for i, (label, value, color) in enumerate(cards):
        x = outer + i * (cw + gap)
        parts.append(f'<rect x="{x}" y="{cy}" width="{cw}" height="{ch}" rx="20" fill="{p["panel2"]}" stroke="{p["border"]}"/>')
        parts.append(f'<rect x="{x}" y="{cy}" width="{cw}" height="8" rx="4" fill="{color}"/>')
        parts.append(
            f'<text x="{x + cw/2}" y="{cy + 78}" text-anchor="middle" fill="{color}" font-family="{FONT}" font-size="64" font-weight="800">{value}</text>'
        )
        parts.append(
            f'<text x="{x + cw/2}" y="{cy + 122}" text-anchor="middle" fill="{p["text"]}" font-family="{FONT}" font-size="28" font-weight="800">{label}</text>'
        )

    parts.append(
        f'<text x="56" y="500" fill="{p["muted"]}" font-family="{FONT}" font-size="26" font-weight="700">Systems · Cloud · Product · Delivery — shipping through review, not decks.</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    commit = latest_commit()
    prs = pr_stats()
    today = datetime.now(IST).strftime("%d %b %Y")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, palette in THEMES.items():
        (OUT / f"work-{name}.svg").write_text(work_svg(palette, commit, prs, today), encoding="utf-8")
    print("work card ←", commit["sha"], "|", prs, "|", today)


if __name__ == "__main__":
    main()

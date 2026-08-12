#!/usr/bin/env python3
"""Regenerate Work cards with latest commit info (updates on every push)."""

from __future__ import annotations

import html
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "v3"
W = 1800
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"

THEMES = {
    "dark": dict(
        bg="#070B12",
        panel="#0E1520",
        panel2="#121A27",
        border="#243041",
        text="#F2F6FC",
        muted="#93A1B5",
        faint="#66768C",
        accent="#4DA3FF",
        accent2="#8AC2FF",
    ),
    "light": dict(
        bg="#F4F7FB",
        panel="#FFFFFF",
        panel2="#EEF3F9",
        border="#D0DAE6",
        text="#0B1220",
        muted="#5C6B80",
        faint="#8A97A8",
        accent="#1769E0",
        accent2="#0B4EBA",
    ),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def latest_commit() -> dict:
    sha = git("log", "-1", "--format=%h")
    subject = git("log", "-1", "--format=%s")
    # ISO date from git
    iso = git("log", "-1", "--format=%cI")
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    secs = int(delta.total_seconds())
    if secs < 60:
        rel = "just now"
    elif secs < 3600:
        rel = f"{secs // 60}m ago"
    elif secs < 86400:
        rel = f"{secs // 3600}h ago"
    else:
        rel = f"{secs // 86400}d ago"
    # Keep subject short for SVG
    subj = subject.strip()
    if len(subj) > 72:
        subj = subj[:69] + "…"
    return {"sha": sha, "subject": subj, "rel": rel, "iso": iso}


def work_svg(p: dict, commit: dict) -> str:
    items = [
        ("Systems", "Service platforms & APIs with clear contracts"),
        ("Cloud", "Event-driven AWS workloads that stay quiet"),
        ("Product", "Next.js when ownership spans the stack"),
        ("Delivery", "GitOps, deploy paths, observability"),
    ]
    card_w, card_h, gap = 820, 120, 28
    top = 168
    h = top + 2 * (card_h + gap) + 36
    sha = html.escape(commit["sha"])
    subject = html.escape(commit["subject"])
    rel = html.escape(commit["rel"])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Work" text-rendering="geometricPrecision">',
        f'<rect width="{W}" height="{h}" rx="24" fill="{p["panel"]}" stroke="{p["border"]}"/>',
        # Heading
        f'<text x="56" y="58" fill="{p["text"]}" font-family="{FONT}" font-size="32" font-weight="700">Work</text>',
        f'<rect x="56" y="76" width="72" height="4" rx="2" fill="{p["accent"]}"/>',
        # Dynamic status strip — updates every commit
        f'<rect x="56" y="100" width="{W-112}" height="48" rx="14" fill="{p["panel2"]}" stroke="{p["border"]}"/>',
        f'<text x="80" y="131" fill="{p["accent"]}" font-family="{MONO}" font-size="18">latest</text>',
        f'<text x="180" y="131" fill="{p["faint"]}" font-family="{MONO}" font-size="18">{sha}</text>',
        f'<text x="280" y="131" fill="{p["text"]}" font-family="{FONT}" font-size="20">{subject}</text>',
        f'<text x="{W-80}" y="131" text-anchor="end" fill="{p["muted"]}" font-family="{FONT}" font-size="18">{rel}</text>',
    ]
    positions = [
        (56, top),
        (56 + card_w + gap, top),
        (56, top + card_h + gap),
        (56 + card_w + gap, top + card_h + gap),
    ]
    for (x, y), (title, desc) in zip(positions, items):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="18" fill="{p["panel2"]}" stroke="{p["border"]}"/>'
        )
        parts.append(f'<circle cx="{x+40}" cy="{y+60}" r="8" fill="{p["accent"]}"/>')
        parts.append(
            f'<text x="{x+70}" y="{y+52}" fill="{p["text"]}" font-family="{FONT}" font-size="24" font-weight="650">{title}</text>'
        )
        parts.append(
            f'<text x="{x+70}" y="{y+86}" fill="{p["muted"]}" font-family="{FONT}" font-size="20">{html.escape(desc)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    commit = latest_commit()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, palette in THEMES.items():
        (OUT / f"work-{name}.svg").write_text(work_svg(palette, commit), encoding="utf-8")
    print(f"updated work cards ← {commit['sha']} {commit['subject']} ({commit['rel']})")


if __name__ == "__main__":
    main()

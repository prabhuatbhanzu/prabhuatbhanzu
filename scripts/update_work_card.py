#!/usr/bin/env python3
"""Regenerate Work cards — light type, tight layout, focus areas."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "v3"
W = 2000
IST = ZoneInfo("Asia/Kolkata")
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
THEMES = {
    "dark": dict(panel="#0E1520", panel2="#141C28", border="#2A3648", text="#E8EEF6", muted="#9AA8BC", accent="#5EB1FF"),
    "light": dict(panel="#FFFFFF", panel2="#F3F7FC", border="#D0DAE6", text="#121926", muted="#5B6B80", accent="#1769E0"),
}
ITEMS = [
    ("Systems", "APIs and service platforms with clear contracts"),
    ("Cloud", "Event-driven AWS paths that stay quiet in prod"),
    ("Product", "Full-stack when shipping needs one owner"),
    ("Delivery", "GitOps, deploys, and observability loops"),
]

def work_svg(p, today):
    card_w, card_h, gap = 900, 112, 20
    top = 118
    h = top + 2 * (card_h + gap) + 28
    positions = [(56, top), (56 + card_w + gap, top), (56, top + card_h + gap), (56 + card_w + gap, top + card_h + gap)]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Work" text-rendering="geometricPrecision">',
        f'<rect width="{W}" height="{h}" rx="24" fill="{p["panel"]}" stroke="{p["border"]}"/>',
        f'<text x="56" y="52" fill="{p["text"]}" font-family="{FONT}" font-size="30" font-weight="600">Work</text>',
        f'<text x="{W-56}" y="52" text-anchor="end" fill="{p["muted"]}" font-family="{MONO}" font-size="18" font-weight="500">{today}</text>',
        f'<rect x="56" y="68" width="56" height="3" rx="1.5" fill="{p["accent"]}"/>',
    ]
    for (x, y), (title, desc) in zip(positions, ITEMS):
        parts += [
            f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="16" fill="{p["panel2"]}" stroke="{p["border"]}"/>',
            f'<circle cx="{x+36}" cy="{y+56}" r="5" fill="{p["accent"]}"/>',
            f'<text x="{x+58}" y="{y+48}" fill="{p["text"]}" font-family="{FONT}" font-size="24" font-weight="600">{title}</text>',
            f'<text x="{x+58}" y="{y+78}" fill="{p["muted"]}" font-family="{FONT}" font-size="20" font-weight="500">{desc}</text>',
        ]
    parts.append("</svg>")
    return "\n".join(parts)

def main():
    today = datetime.now(IST).strftime("%d %b %Y")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, palette in THEMES.items():
        (OUT / f"work-{name}.svg").write_text(work_svg(palette, today), encoding="utf-8")
    print("work", today)

if __name__ == "__main__":
    main()

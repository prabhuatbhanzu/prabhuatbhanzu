#!/usr/bin/env python3
"""Generate real contribution graphics from GitHub GraphQL (same source as the profile graph)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGIN = os.environ.get("GITHUB_LOGIN", "prabhuatbhanzu")


def gh_graphql(query: str, variables: dict) -> dict:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".graphql", delete=False) as f:
        f.write(query)
        qpath = f.name
    try:
        cmd = ["gh", "api", "graphql", "-F", f"query=@{qpath}"]
        for k, v in variables.items():
            cmd.extend(["-f", f"{k}={v}"])
        out = subprocess.check_output(cmd, text=True)
    finally:
        Path(qpath).unlink(missing_ok=True)
    data = json.loads(out)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


QUERY = """
query($login:String!){
  user(login:$login){
    name
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""

# GitHub-like palettes (empty → high)
PALETTES = {
    "dark": {
        "bg": "#0D1117",
        "panel": "#0D1117",
        "border": "#21262D",
        "text": "#E6EDF3",
        "muted": "#8B949E",
        "accent": "#58A6FF",
        "levels": ["#161B22", "#0E4429", "#006D32", "#26A641", "#39D353"],
    },
    "light": {
        "bg": "#FFFFFF",
        "panel": "#FFFFFF",
        "border": "#D0D7DE",
        "text": "#1F2328",
        "muted": "#656D76",
        "accent": "#0969DA",
        "levels": ["#EBEDF0", "#9BE9A8", "#40C463", "#30A14E", "#216E39"],
    },
}


def level_for(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 1:
        return 4
    # quartile-ish mapping similar to GitHub
    q = count / max_count
    if q <= 0.25:
        return 1
    if q <= 0.50:
        return 2
    if q <= 0.75:
        return 3
    return 4


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    """Return (current_streak, longest_streak)."""
    # days sorted ascending by date
    ordered = sorted(days, key=lambda d: d["date"])
    longest = cur = 0
    for d in ordered:
        if d["contributionCount"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    # current streak from the end
    current = 0
    for d in reversed(ordered):
        # ignore future/today-empty trailing? count consecutive from latest day with activity chain ending today or yesterday
        day = date.fromisoformat(d["date"])
        if d["contributionCount"] > 0:
            current += 1
        else:
            # allow today empty if no contrib yet
            if day == date.today() and current == 0:
                continue
            break
    return current, longest


def month_labels(weeks: list) -> list[tuple[int, str]]:
    """x-index (week col) -> month short name when month changes."""
    labels = []
    prev = None
    for i, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue
        first = week["contributionDays"][0]["date"]
        m = datetime.fromisoformat(first).strftime("%b")
        if m != prev:
            labels.append((i, m))
            prev = m
    return labels


def render_heatmap(theme: str, cal: dict, stats: dict) -> str:
    p = PALETTES[theme]
    weeks = cal["weeks"]
    all_days = [d for w in weeks for d in w["contributionDays"]]
    max_count = max((d["contributionCount"] for d in all_days), default=0)

    cell, gap = 11, 3
    left, top = 36, 48
    cols = len(weeks)
    width = left + cols * (cell + gap) + 24
    height = top + 7 * (cell + gap) + 56

    # month labels
    labels = month_labels(weeks)
    label_svg = []
    for col, name in labels:
        x = left + col * (cell + gap)
        label_svg.append(
            f'<text x="{x}" y="28" fill="{p["muted"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11">{name}</text>'
        )

    dow = ["", "Mon", "", "Wed", "", "Fri", ""]
    dow_svg = []
    for i, name in enumerate(dow):
        if not name:
            continue
        y = top + i * (cell + gap) + cell - 1
        dow_svg.append(
            f'<text x="4" y="{y}" fill="{p["muted"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="10">{name}</text>'
        )

    cells = []
    for ci, week in enumerate(weeks):
        for day in week["contributionDays"]:
            # GitHub weekday: 0=Sunday ... 6=Saturday — match native graph rows
            # GraphQL weekday: Monday=1 ... Sunday=7 in some APIs; contributionDays include weekday 0-6 Sun-Sat per GitHub docs
            wd = day.get("weekday")
            # Prefer order in week array position if weekday missing
            if wd is None:
                continue
            # GitHub profile uses Sun→Sat top→bottom. API weekday: 0 Sunday.
            row = wd
            x = left + ci * (cell + gap)
            y = top + row * (cell + gap)
            lvl = level_for(day["contributionCount"], max_count)
            color = p["levels"][lvl]
            title = f'{day["date"]}: {day["contributionCount"]} contribution{"s" if day["contributionCount"] != 1 else ""}'
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color}"><title>{title}</title></rect>'
            )

    # legend
    legend_y = top + 7 * (cell + gap) + 22
    legend = [
        f'<text x="{left}" y="{legend_y}" fill="{p["muted"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11">Less</text>'
    ]
    lx = left + 34
    for i, c in enumerate(p["levels"]):
        legend.append(f'<rect x="{lx + i * (cell + gap)}" y="{legend_y - 10}" width="{cell}" height="{cell}" rx="2" fill="{c}"/>')
    legend.append(
        f'<text x="{lx + 5 * (cell + gap) + 6}" y="{legend_y}" fill="{p["muted"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11">More</text>'
    )

    total = stats["total"]
    header = (
        f'<text x="{left}" y="16" fill="{p["text"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="14" font-weight="600">'
        f'{total:,} contributions in the last year</text>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{total} contributions in the last year">
  <rect width="100%" height="100%" rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>
  {header}
  {''.join(label_svg)}
  {''.join(dow_svg)}
  {''.join(cells)}
  {''.join(legend)}
</svg>
'''


def render_stats(theme: str, stats: dict) -> str:
    p = PALETTES[theme]
    cards = [
        ("Contributions", f'{stats["total"]:,}'),
        ("Active days", f'{stats["active_days"]:,}'),
        ("Current streak", f'{stats["current_streak"]}'),
        ("Longest streak", f'{stats["longest_streak"]}'),
    ]
    w, h = 760, 110
    gap = 16
    cw = (w - 40 - 3 * gap) // 4
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Contribution statistics">',
        f'<rect width="100%" height="100%" rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    for i, (label, value) in enumerate(cards):
        x = 20 + i * (cw + gap)
        parts.append(f'<rect x="{x}" y="16" width="{cw}" height="78" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>')
        parts.append(
            f'<text x="{x + 14}" y="42" fill="{p["muted"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="11">{label}</text>'
        )
        parts.append(
            f'<text x="{x + 14}" y="72" fill="{p["accent"]}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="24" font-weight="700">{value}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_divider(theme: str) -> str:
    p = PALETTES[theme]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="16" viewBox="0 0 720 16" role="img" aria-hidden="true">
  <defs>
    <linearGradient id="d" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{p["accent"]}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{p["accent"]}" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="{p["accent"]}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="7" width="720" height="1" fill="url(#d)"/>
</svg>
'''


def main() -> int:
    data = gh_graphql(QUERY, {"login": LOGIN})
    cal = data["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, longest = compute_streaks(days)
    stats = {
        "total": cal["totalContributions"],
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
        "current_streak": current,
        "longest_streak": longest,
    }
    print("stats", stats)

    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        (ASSETS / f"contributions-{theme}.svg").write_text(render_heatmap(theme, cal, stats), encoding="utf-8")
        (ASSETS / f"stats-{theme}.svg").write_text(render_stats(theme, stats), encoding="utf-8")
        (ASSETS / f"divider-{theme}.svg").write_text(render_divider(theme), encoding="utf-8")
    # keep default divider for simplicity pointing to dark; README uses picture
    (ASSETS / "divider.svg").write_text(render_divider("dark"), encoding="utf-8")
    print("wrote assets to", ASSETS)
    return 0


if __name__ == "__main__":
    sys.exit(main())

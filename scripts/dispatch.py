#!/usr/bin/env python3
"""
The Hedge — automated dispatch generator (EXPERIMENTAL, 2026-06-15).

The full loop, in one script:
  1. GATHER  real data: NWS weather (Algoma WI) + phenology + moon + sabbat
  2. WRITE   a short dispatch from that data via the OpenAI API
  3. FILE    it as markdown into the site's `dispatches` collection
  4. PUBLISH (with --publish) git commit + push -> Cloudflare auto-deploys

Usage:
  python3 scripts/dispatch.py                # gather + write + file (dry, no push)
  python3 scripts/dispatch.py --publish      # ...and commit + push (goes live)
  python3 scripts/dispatch.py --date 2026-06-20   # override date (testing)

Env:
  OPENAI_API_KEY   required
  OPENAI_MODEL     optional (default: gpt-5.1)
"""

import argparse, csv, datetime, json, os, pathlib, subprocess, sys, urllib.request

ALGOMA_LAT, ALGOMA_LON = 44.6136, -87.4326
UA = "thehedge-dispatch (don@krumpos.org)"

SITE = pathlib.Path(__file__).resolve().parents[1]            # .../thehedge
RELIQUARY = SITE.parent / "reliquary"
PHENOLOGY = RELIQUARY / "knowledge/phenology/door-county-2026.csv"
MOON = RELIQUARY / "knowledge/almanac/moon-phases-2026.csv"
SABBATS = RELIQUARY / "knowledge/almanac/sabbats-2026.csv"
OUT_DIR = SITE / "src/content/dispatches"

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.1")


# ---------- HTTP ----------
def http_json(url, headers=None, data=None, method="GET"):
    req = urllib.request.Request(
        url, headers=headers or {}, data=data, method=method
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


# ---------- 1. GATHER ----------
def get_weather():
    pts = http_json(
        f"https://api.weather.gov/points/{ALGOMA_LAT},{ALGOMA_LON}",
        {"User-Agent": UA},
    )
    fc = http_json(pts["properties"]["forecast"], {"User-Agent": UA})
    p = fc["properties"]["periods"][0]
    short = f"{p['name']}: {p['shortForecast']}, {p['temperature']}°{p['temperatureUnit']}, wind {p['windSpeed']} {p['windDirection']}"
    return {"short": short, "detailed": p["detailedForecast"], "name": p["name"]}


def _read_calendar(path):
    """CSV rows -> list of (date, content)."""
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                d = datetime.date(int(r["Year"]), _month_num(r["Month"]), int(r["Day"]))
            except (ValueError, KeyError):
                continue
            rows.append((d, r["Content"]))
    return rows


def _month_num(name):
    return datetime.datetime.strptime(name[:3], "%b").month


def get_phenology(day):
    return [c for (d, c) in _read_calendar(PHENOLOGY) if d == day]


def get_moon(day):
    cal = _read_calendar(MOON)
    nearest = min(cal, key=lambda x: abs((x[0] - day).days))
    delta = (nearest[0] - day).days
    when = "today" if delta == 0 else (f"in {delta} days" if delta > 0 else f"{-delta} days ago")
    return f"{nearest[1]} ({when})"


def get_sabbat(day):
    cal = sorted(_read_calendar(SABBATS))
    upcoming = [(d, c) for (d, c) in cal if d >= day]
    past = [(d, c) for (d, c) in cal if d < day]
    nxt = upcoming[0] if upcoming else None
    prev = past[-1] if past else None
    out = []
    if prev:
        out.append(f"Most recent: {prev[1]} ({(day - prev[0]).days} days ago)")
    if nxt:
        out.append(f"Next: {nxt[1]} (in {(nxt[0] - day).days} days)")
    return out


def gather(day):
    return {
        "date": day,
        "weather": get_weather(),
        "phenology": get_phenology(day),
        "moon": get_moon(day),
        "sabbat": get_sabbat(day),
    }


# ---------- 2. WRITE ----------
SYSTEM = """You are writing a short dispatch for "The Hedge" — a place-anchored \
publication from Algoma, Wisconsin, a small Lake Michigan town. The voice is in \
the lineage of Stewart Brand, Wendell Berry, and Robert Macfarlane: grounded, \
observational, unhurried, warm, attentive to weather, plants, work, and the \
turning of the year. Write as someone who lives at the edge of the village and \
notices things. Use the real data provided — weather, phenology, moon, season — \
as the spine of the piece. ~350-550 words.

Return the TITLE on the first line (just the title, no label), then a blank \
line, then the dispatch body in plain markdown (no headings)."""


def build_prompt(packet):
    w = packet["weather"]
    lines = [
        f"Date: {packet['date'].strftime('%A, %B %-d, %Y')}",
        f"Weather (Algoma, WI): {w['short']}",
        f"  Detail: {w['detailed']}",
        f"Moon: {packet['moon']}",
    ]
    if packet["sabbat"]:
        lines.append("Wheel of the year: " + "; ".join(packet["sabbat"]))
    if packet["phenology"]:
        lines.append("Phenology today (Door County preserves):")
        lines += [f"  - {e}" for e in packet["phenology"]]
    else:
        lines.append("Phenology today: (no specific events listed for this date)")
    return "\n".join(lines)


def write_dispatch(packet):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("ERROR: OPENAI_API_KEY not set")
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": build_prompt(packet)},
            ],
            "max_completion_tokens": 1200,
        }
    ).encode()
    resp = http_json(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        data=body,
        method="POST",
    )
    text = resp["choices"][0]["message"]["content"].strip()
    parts = text.split("\n", 1)
    title = parts[0].strip().lstrip("#").strip().strip('"')
    prose = parts[1].strip() if len(parts) > 1 else ""
    return title, prose


# ---------- 3. FILE ----------
def yaml_escape(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def file_dispatch(packet, title, prose):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = packet["date"].isoformat()
    fm = [
        "---",
        f"title: {yaml_escape(title)}",
        f"date: {slug}",
        f"weather: {yaml_escape(packet['weather']['short'])}",
        "generated: true",
        f"model: {MODEL}",
        "---",
        "",
        prose,
        "",
    ]
    path = OUT_DIR / f"{slug}.md"
    path.write_text("\n".join(fm))
    return path


# ---------- 4. PUBLISH ----------
def publish(path):
    rel = path.relative_to(SITE)
    subprocess.run(["git", "-C", str(SITE), "add", str(rel)], check=True)
    subprocess.run(
        ["git", "-C", str(SITE), "commit", "-q", "-m", f"Dispatch: {path.stem} (automated)"],
        check=True,
    )
    subprocess.run(["git", "-C", str(SITE), "pull", "--rebase", "-q"], check=False)
    subprocess.run(["git", "-C", str(SITE), "push", "-q"], check=True)


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--publish", action="store_true", help="commit + push -> deploy")
    args = ap.parse_args()

    day = (
        datetime.date.fromisoformat(args.date)
        if args.date
        else datetime.date.today()
    )

    print(f"[1/4] gathering data for {day} ...")
    packet = gather(day)
    print(f"      weather: {packet['weather']['short']}")
    print(f"      moon:    {packet['moon']}")
    print(f"      phenology: {packet['phenology'] or '(none)'}")

    print(f"[2/4] writing dispatch via {MODEL} ...")
    title, prose = write_dispatch(packet)
    print(f"      title: {title}  ({len(prose.split())} words)")

    print("[3/4] filing markdown ...")
    path = file_dispatch(packet, title, prose)
    print(f"      wrote {path.relative_to(SITE.parent)}")

    if args.publish:
        print("[4/4] publishing (commit + push) ...")
        publish(path)
        print("      pushed -> Cloudflare will deploy")
    else:
        print("[4/4] skipped publish (use --publish to go live)")


if __name__ == "__main__":
    main()

"""Builds docs/launches.json: a tiny rocket-launch feed for VJ's Garmin watch.

The Space Devs API has nice mission descriptions, but its responses are far too big
for the watch to download through the phone. This runs hourly on GitHub Actions,
keeps only what the watch shows, and GitHub Pages serves the result.

Output: {"at": epoch, "list": [[mission, rocket, agency, epoch, status, type, place, description], ...]}
(same order the watch app already uses, plus the description at the end).
Standard library only.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime

API = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?mode=normal&limit=20&hide_recent_previous=true"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "launches.json")
MAX = 8

AGENCIES = [
    ("Indian Space", "ISRO"),
    ("National Aeronautics", "NASA"),
    ("United Launch", "ULA"),
    ("China Aerospace", "China"),
    ("Mitsubishi", "Japan"),
    ("Japan Aerospace", "Japan"),
    ("Space Exploration Technologies", "SpaceX"),
]
STATES = {"FL": "Florida", "CA": "California", "TX": "Texas", "VA": "Virginia", "AK": "Alaska"}
COUNTRIES = ["China", "India", "Japan", "New Zealand", "French Guiana", "Kazakhstan", "Russia"]


def agency(name):
    for key, short in AGENCIES:
        if key in name:
            return short
    return name if len(name) <= 18 else name[:18]


def place(location):
    for code, state in STATES.items():
        if f", {code}," in location:
            return state
    for country in COUNTRIES:
        if country in location:
            return country
    return ""


def first_sentence(text, limit=160):
    text = " ".join((text or "").split())
    if not text or text.startswith("Details TBD"):
        return ""
    dot = text.find(". ")
    s = text[: dot + 1] if dot != -1 else text
    return s if len(s) <= limit else s[: limit - 3].rsplit(" ", 1)[0] + "..."


def build(data):
    out = []
    for r in data.get("results", []):
        rocket, _, mission = r["name"].partition(" | ")
        mission = mission or rocket
        if "Starlink" in mission or "Unknown Payload" in mission:
            continue
        m = r.get("mission") or {}
        lsp = (r.get("launch_service_provider") or {}).get("name", "")
        net = int(datetime.fromisoformat(r["net"].replace("Z", "+00:00")).timestamp())
        loc = ((r.get("pad") or {}).get("location") or {}).get("name", "")
        out.append([
            mission,
            rocket,
            agency(lsp),
            net,
            (r.get("status") or {}).get("abbrev", ""),
            m.get("type") or "",
            place(loc),
            first_sentence(m.get("description")),
        ])
        if len(out) == MAX:
            break
    return out


def main():
    try:
        req = urllib.request.Request(API, headers={"User-Agent": "vj-watch-feed"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
    except Exception as e:  # rate limited or down: keep the last good file
        print("fetch failed, keeping previous feed:", e)
        return 0
    feed = {"at": int(datetime.now().timestamp()), "list": build(data)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(feed, f, separators=(",", ":"), ensure_ascii=False)
    print(f"wrote {len(feed['list'])} launches, {os.path.getsize(OUT)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

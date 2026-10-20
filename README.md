# watch-feed

Tiny hourly feed for VJ's Garmin vivoactive 5 Connect IQ apps.

- `build_launches.py` trims The Space Devs launch API down to what the watch shows
  (mission, rocket, agency, time, place, one-line description) and writes `docs/launches.json`.
- `.github/workflows/launches.yml` runs it every hour; GitHub Pages serves `docs/`.

Only public launch data lives here.

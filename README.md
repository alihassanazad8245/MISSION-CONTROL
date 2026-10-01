# Mission Control

A live, interactive terminal space dashboard — real-time ISS tracking on an
actual coastline world map, an animated top-down solar system driven by real
orbital mechanics, tonight's Moon phase and visible planets, upcoming rocket
launches, near-Earth asteroids, space weather, and today's full-disc photo
of Earth rendered in full colour, right in your terminal.

Defaults to **Pakistan Standard Time and Islamabad** for weather/sky — pass
`--location` for anywhere else.

![Mission Control](docs/screenshots/01-dashboard.png)

## Why it's different

- **A real world map**, built from actual Natural Earth coastline data and
  rendered in Unicode Braille (4x the resolution of plain block characters) —
  not a hand-drawn blob.
- **The ISS actually moves smoothly** between API refreshes — its ground
  track is extrapolated from two real fixes using great-circle math at its
  true velocity and heading, not just jumping every few seconds.
- **The solar system is animated with real orbital mechanics** (Keplerian
  elements, the same approach JPL publishes for approximate positions) —
  press `t` to time-warp and watch planets actually move at 30 min/sec,
  6 hours/sec, or 3 days/sec.
- **The Moon phase is computed, not looked up** — real lunar theory
  (Meeus), verified against the actual September 2026 full moon to within
  3 minutes.
- **Today's Earth photo renders in real color** using half-block terminal
  art — an actual downloaded photo, not a broken link or a caption-only
  placeholder.
- Every data source degrades gracefully on its own — if one API is down,
  that panel alone shows "Unavailable", the rest keep working.

## Tabs

| Tab | What's in it |
|---|---|
| Overview | Pakistan clock, local weather, ISS quick stats, next launch |
| ISS Tracker | Live world map with the ISS's real position and heading |
| Solar System | Animated top-down orbital diagram (press `t` to time-warp) |
| Sky Tonight | Real Moon phase art, and altitude/azimuth for the Moon + 5 planets |
| Launches & Asteroids | Upcoming launches with live countdowns; today's close approaches |
| Space Weather | Kp-index, radio/radiation/geomagnetic storm scales, aurora verdict |
| Earth Today | Today's full-disc Earth photo (NASA EPIC), rendered in colour |

## Requirements

Python 3.9+ and an internet connection. Most sources need no signup.
NASA's endpoints work immediately with the public `DEMO_KEY`; for heavier
use, get a free instant key at [api.nasa.gov](https://api.nasa.gov) and set
`NASA_API_KEY`.

## Installation

```bash
cd MISSION-CONTROL
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

```bash
python main.py                                      # Pakistan (Islamabad) by default
python main.py --location 24.86,67.00 --label "Karachi"
```

**Keys:** `t` cycle time-warp speed (Solar System tab) · `r` force-refresh all data · `q` quit

## Tests

```bash
pip install pytest
pytest
```

17 tests covering the astronomy engine (validated against real published
almanac data) and every API source module (mocked against the real
documented response shapes).

## Project structure

```
MISSION-CONTROL/
├── main.py
├── requirements.txt
├── pytest.ini
├── data/                       # saved location (git-ignored)
├── tests/
└── mission_control/
    ├── astro/                   # kepler.py, sun_moon.py, planets.py, groundtrack.py
    ├── sources/                   # iss, launches, neo, space_weather, photos, local_weather
    ├── render/                     # worldmap.py, orbits.py, moonphase.py, imageart.py
    ├── app/                         # Textual TUI: app.py, datahub.py, widgets.py
    ├── cli.py, config.py, models.py, settings.py, errors.py
```

## Known limitations

- Planet positions use JPL's approximate Keplerian elements (valid
  1800–2050, accurate to about an arc-minute) — not a full numerical
  integrator, but the same method used for most "where is Mars tonight"
  tools.
- The Solar System diagram's ring spacing is schematic (even spacing by
  orbital rank), not physically to scale — true relative distances would
  crush Mercury into the Sun's own character cell. Angles are always real.
- Launch Library 2 allows only ~15 anonymous requests/hour, so launches
  refresh every 10 minutes.
- Earth Today needs one extra request to fetch the actual image bytes; on a
  slow connection the photo may take a moment to appear after the tab loads.

## License

MIT License. See [LICENSE](LICENSE).

---

Built by **Ali Hassan** — Instagram: [@ali_hassan8245](https://instagram.com/ali_hassan8245)

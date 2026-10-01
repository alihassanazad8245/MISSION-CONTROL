"""Mission Control - the Textual TUI application."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Digits, Footer, Header, Static, TabbedContent, TabPane

from .. import __app_name__, __author__, __instagram__, __version__
from ..astro.groundtrack import GroundTrackExtrapolator
from ..astro.sun_moon import moon_elongation, moon_illumination, moon_events, phase_name, sun_events
from ..astro.timeutil import julian_date, now_utc, to_pkt
from ..astro.planets import VISIBLE_PLANETS, planet_altaz
from ..astro.sun_moon import moon_altaz
from ..config import DASHBOARD_TICK_SECONDS
from ..mapping_compat import format_duration
from ..render.imageart import render_image_bytes
from ..render.moonphase import render_moon
from ..render.orbits import render_orbits
from ..render.worldmap import render_map
from .datahub import DataHub
from .widgets import LiveRenderable

_ISS_TRAIL_SECONDS = 900


class MissionControlApp(App):
    CSS_PATH = "styles.tcss"
    TITLE = __app_name__
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "cycle_warp", "Time-warp"),
        ("r", "force_refresh", "Refresh now"),
    ]

    def __init__(self, hub: DataHub) -> None:
        super().__init__()
        self.hub = hub
        self.track = GroundTrackExtrapolator()
        self._trail: list[tuple[float, float, datetime]] = []
        self._warp_levels = [1, 60 * 30, 60 * 60 * 6, 60 * 60 * 24 * 3]
        self._warp_labels = ["Real time", "30x/min \u2192 30 min/s", "6 hr/s", "3 days/s"]
        self._warp_index = 0
        self._sim_start_real = now_utc()
        self._sim_start_value = now_utc()

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with TabbedContent(initial="overview"):
            with TabPane("Overview", id="overview"):
                yield from self._overview_pane()
            with TabPane("ISS Tracker", id="iss"):
                yield LiveRenderable(self._render_iss, id="iss_panel")
            with TabPane("Solar System", id="orbits"):
                yield LiveRenderable(self._render_orbits, id="orbits_panel")
            with TabPane("Sky Tonight", id="sky"):
                with Horizontal():
                    yield LiveRenderable(self._render_moon, id="moon_panel")
                    yield LiveRenderable(self._render_sky_table, id="sky_table_panel")
            with TabPane("Launches & Asteroids", id="launches"):
                with Vertical():
                    yield LiveRenderable(self._render_launches, id="launches_panel")
                    yield LiveRenderable(self._render_neo, id="neo_panel")
            with TabPane("Space Weather", id="weather"):
                yield LiveRenderable(self._render_space_weather, id="space_weather_panel")
            with TabPane("Earth Today", id="earth"):
                yield LiveRenderable(self._render_earth_photo, id="earth_panel")
        yield Footer()

    def _overview_pane(self) -> ComposeResult:
        with Vertical(id="overview_root"):
            yield Digits("00:00:00", id="pkt_clock")
            yield Static(id="overview_sub")
            with Horizontal():
                yield LiveRenderable(self._render_overview_weather, id="overview_weather", classes="card")
                yield LiveRenderable(self._render_overview_iss, id="overview_iss", classes="card")
                yield LiveRenderable(self._render_overview_launch, id="overview_launch", classes="card")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def on_mount(self) -> None:
        self.hub.tick()
        self.set_interval(DASHBOARD_TICK_SECONDS, self._on_tick)

    def simulated_now(self) -> datetime:
        multiplier = self._warp_levels[self._warp_index]
        elapsed_real = (now_utc() - self._sim_start_real).total_seconds()
        return self._sim_start_value + timedelta(seconds=elapsed_real * multiplier)

    def action_cycle_warp(self) -> None:
        self._sim_start_value = self.simulated_now()
        self._sim_start_real = now_utc()
        self._warp_index = (self._warp_index + 1) % len(self._warp_levels)
        self.notify(f"Time-warp: {self._warp_labels[self._warp_index]}")

    def action_force_refresh(self) -> None:
        for slot in (self.hub.iss, self.hub.launches, self.hub.neo, self.hub.space_weather,
                    self.hub.apod, self.hub.epic, self.hub.weather):
            slot.updated_at = 0.0
        self.hub.tick()
        self.notify("Refreshing all data sources…")

    def _on_tick(self) -> None:
        self.hub.tick()
        pos = self.hub.iss.value
        if pos is not None:
            self.track.update(pos.timestamp, pos.latitude, pos.longitude)
            self._trail.append((pos.latitude, pos.longitude, pos.timestamp))
            cutoff = now_utc() - timedelta(seconds=_ISS_TRAIL_SECONDS)
            self._trail = [t for t in self._trail if t[2] >= cutoff]

        try:
            self.query_one("#pkt_clock", Digits).update(to_pkt(now_utc()).strftime("%H:%M:%S"))
            self.query_one("#overview_sub", Static).update(self._overview_subtitle())
        except Exception:  # noqa: BLE001 - widget not mounted yet on first tick
            pass

        for widget_id in ("iss_panel", "orbits_panel", "moon_panel", "sky_table_panel",
                          "launches_panel", "neo_panel", "space_weather_panel", "earth_panel",
                          "overview_weather", "overview_iss", "overview_launch"):
            try:
                self.query_one(f"#{widget_id}", LiveRenderable).refresh_content()
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------------ #
    # Overview
    # ------------------------------------------------------------------ #

    def _overview_subtitle(self) -> Text:
        pkt = to_pkt(now_utc())
        return Text(f"{pkt.strftime('%A, %d %B %Y')}  •  Pakistan Standard Time  •  "
                   f"{self.hub.location_label}", style="dim cyan", justify="center")

    def _render_overview_weather(self) -> Panel:
        w = self.hub.weather.value
        if w is None:
            return _unavailable("LOCAL WEATHER", self.hub.weather.error)
        body = Text()
        body.append(f"{w.temperature_c:.0f}\u00b0C", style="bold white")
        body.append(f"  feels {w.apparent_c:.0f}\u00b0C\n", style="dim")
        body.append(f"{w.weather_text}\n", style="cyan")
        body.append(f"H {w.daily_max_c:.0f}\u00b0 / L {w.daily_min_c:.0f}\u00b0   "
                    f"Humidity {w.humidity_pct:.0f}%\n", style="white")
        body.append(f"Wind {w.wind_kmh:.0f} km/h", style="white")
        return Panel(body, title=f"[bold]\U0001F324  {w.location_label}[/bold]", border_style="cyan")

    def _render_overview_iss(self) -> Panel:
        pos = self.hub.iss.value
        if pos is None:
            return _unavailable("ISS", self.hub.iss.error)
        body = Text()
        body.append(f"{pos.latitude:.1f}\u00b0, {pos.longitude:.1f}\u00b0\n", style="bold white")
        body.append(f"Altitude {pos.altitude_km:,.0f} km\n", style="white")
        body.append(f"{pos.velocity_kmh:,.0f} km/h\n", style="white")
        body.append("\u2600 Daylight" if pos.visibility == "daylight" else "\U0001F311 Eclipsed", style="yellow")
        return Panel(body, title="[bold]\U0001F6F0  ISS NOW[/bold]", border_style="cyan")

    def _render_overview_launch(self) -> Panel:
        items = self.hub.launches.value
        if not items:
            return _unavailable("NEXT LAUNCH", self.hub.launches.error)
        launch = items[0]
        delta = (launch.net - datetime.now(timezone.utc)).total_seconds()
        body = Text()
        body.append(f"{launch.name}\n", style="bold white")
        body.append(f"{launch.provider} \u00b7 {launch.rocket}\n", style="dim cyan")
        body.append(format_duration(delta) if delta > 0 else "IN LAUNCH WINDOW", style="bold yellow")
        return Panel(body, title="[bold]\U0001F680  NEXT LAUNCH[/bold]", border_style="cyan")

    # ------------------------------------------------------------------ #
    # ISS Tracker
    # ------------------------------------------------------------------ #

    def _render_iss(self) -> Panel:
        pos = self.hub.iss.value
        if pos is None:
            return _unavailable("ISS TRACKER", self.hub.iss.error)

        sim_now = now_utc()
        live_lat, live_lon = self.track.position_at(sim_now, pos.velocity_kmh)
        trail_points = [(lat, lon) for lat, lon, _ in self._trail]

        markers = {"\u25c9": (self.hub.latitude, self.hub.longitude)}
        map_lines = render_map(96, 34, markers=markers, trail=trail_points)
        map_text = Text("\n".join(map_lines), style="bright_green")
        iss_marker = Text(f"ISS \u2192 lat {live_lat:.2f}, lon {live_lon:.2f}   "
                          f"heading {self.track.heading or 0:.0f}\u00b0", style="bold yellow")

        info = Table.grid(padding=(0, 3))
        info.add_column(style="dim cyan")
        info.add_column(style="white")
        info.add_row("Altitude", f"{pos.altitude_km:,.1f} km")
        info.add_row("Velocity", f"{pos.velocity_kmh:,.0f} km/h")
        info.add_row("Sunlight", "\u2600 Daylight" if pos.visibility == "daylight" else "\U0001F311 Eclipsed")
        info.add_row("Your location", f"\u25c9 {self.hub.location_label}")

        from rich.console import Group
        return Panel(Group(map_text, Text(""), iss_marker, Text(""), info),
                    title="[bold]\U0001F6F0  INTERNATIONAL SPACE STATION \u2014 LIVE[/bold]",
                    border_style="cyan")

    # ------------------------------------------------------------------ #
    # Solar System
    # ------------------------------------------------------------------ #

    def _render_orbits(self) -> Panel:
        sim_now = self.simulated_now()
        diagram = render_orbits(sim_now, 88, 32)
        caption = Text()
        caption.append(f"Simulated: {sim_now.strftime('%Y-%m-%d %H:%M')} UTC   ", style="white")
        caption.append(f"[{self._warp_labels[self._warp_index]}]  ", style="bold yellow")
        caption.append("press 't' to change speed", style="dim")
        from rich.console import Group
        return Panel(Group(diagram, caption), title="[bold]\u2609  THE SOLAR SYSTEM RIGHT NOW[/bold]",
                    border_style="cyan")

    # ------------------------------------------------------------------ #
    # Sky Tonight
    # ------------------------------------------------------------------ #

    def _render_moon(self) -> Panel:
        jd = julian_date(now_utc())
        elong = moon_elongation(jd)
        illum = moon_illumination(jd)
        waxing = elong < 180.0
        art = render_moon(illum, waxing, 16)
        caption = Text(f"{phase_name(elong)}  \u00b7  {illum * 100:.0f}% illuminated", style="bold white")
        from rich.console import Group
        return Panel(Group(Align.center(art), Align.center(caption)),
                    title="[bold]\U0001F311 MOON[/bold]", border_style="cyan")

    def _render_sky_table(self) -> Panel:
        lat, lon = self.hub.latitude, self.hub.longitude
        when = now_utc()
        table = Table(box=None, show_edge=False, pad_edge=False)
        table.add_column("Object", style="white")
        table.add_column("Altitude", style="dim cyan", justify="right")
        table.add_column("Azimuth", style="dim cyan", justify="right")
        table.add_column("Status", style="bold")

        m_alt, m_az = moon_altaz(lat, lon, when)
        table.add_row("Moon", f"{m_alt:.1f}\u00b0", f"{m_az:.1f}\u00b0",
                     "[green]Visible[/green]" if m_alt > 0 else "[dim]Below horizon[/dim]")
        rows = [("Moon", m_alt)]
        for name in VISIBLE_PLANETS:
            alt, az = planet_altaz(name, lat, lon, when)
            rows.append((name, alt))
            table.add_row(name, f"{alt:.1f}\u00b0", f"{az:.1f}\u00b0",
                         "[green]Visible[/green]" if alt > 0 else "[dim]Below horizon[/dim]")

        day_start = when.replace(hour=0, minute=0, second=0, microsecond=0)
        sun_ev = sun_events(lat, lon, day_start)
        moon_ev = moon_events(lat, lon, day_start)

        times = Table.grid(padding=(0, 3))
        times.add_column(style="dim cyan")
        times.add_column(style="white")
        for label, key, src in [("Sunrise", "sunrise", sun_ev), ("Sunset", "sunset", sun_ev),
                                ("Moonrise", "moonrise", moon_ev), ("Moonset", "moonset", moon_ev)]:
            value = src.get(key)
            times.add_row(label, to_pkt(value).strftime("%H:%M PKT") if value else "\u2014")

        from rich.console import Group
        return Panel(Group(table, Text(""), times), title=f"[bold]\U0001F30C SKY \u2014 {self.hub.location_label}[/bold]",
                    border_style="cyan")

    # ------------------------------------------------------------------ #
    # Launches & NEO
    # ------------------------------------------------------------------ #

    def _render_launches(self) -> Panel:
        items = self.hub.launches.value
        if not items:
            return _unavailable("UPCOMING LAUNCHES", self.hub.launches.error)
        table = Table(box=None, show_edge=False, pad_edge=False)
        table.add_column("T-minus", style="bold yellow", width=14)
        table.add_column("Mission", style="white")
        table.add_column("Provider", style="dim cyan")
        now = datetime.now(timezone.utc)
        for launch in items[:6]:
            delta = (launch.net - now).total_seconds()
            countdown = format_duration(delta) if delta > 0 else "LIFTOFF WINDOW"
            table.add_row(countdown, f"{launch.name}\n[dim]{launch.rocket} \u00b7 {launch.location}[/dim]",
                         launch.provider)
        return Panel(table, title="[bold]\U0001F680 UPCOMING LAUNCHES[/bold]", border_style="cyan")

    def _render_neo(self) -> Panel:
        items = self.hub.neo.value
        if not items:
            return _unavailable("NEAR-EARTH OBJECTS TODAY", self.hub.neo.error)
        table = Table(box=None, show_edge=False, pad_edge=False)
        table.add_column("Object", style="white")
        table.add_column("Size (m)", style="dim cyan", justify="right")
        table.add_column("Miss distance", style="white", justify="right")
        table.add_column("Speed", style="dim cyan", justify="right")
        table.add_column("", style="bold red", width=10)
        for obj in items[:5]:
            table.add_row(obj.name, f"{obj.diameter_min_m:.0f}\u2013{obj.diameter_max_m:.0f}",
                         f"{obj.miss_distance_lunar:.1f}\u00d7 lunar dist.",
                         f"{obj.velocity_kmh:,.0f} km/h", "\u26a0 HAZARD" if obj.is_hazardous else "")
        return Panel(table, title="[bold]\u2604  NEAR-EARTH OBJECTS TODAY[/bold]", border_style="cyan")

    # ------------------------------------------------------------------ #
    # Space Weather
    # ------------------------------------------------------------------ #

    def _render_space_weather(self) -> Panel:
        w = self.hub.space_weather.value
        if w is None:
            return _unavailable("SPACE WEATHER", self.hub.space_weather.error)
        table = Table.grid(padding=(0, 3))
        table.add_column(style="dim cyan")
        table.add_column(style="white")
        table.add_row("Planetary Kp-index", f"{w.kp_index:.1f}" if w.kp_index is not None else "N/A")
        table.add_row("Radio blackout", w.radio_blackout_scale)
        table.add_row("Radiation storm", w.radiation_storm_scale)
        table.add_row("Geomagnetic storm", w.geomagnetic_storm_scale)
        verdict = Text(f"\n{w.aurora_verdict}",
                      style="bold green" if "Quiet" in w.aurora_verdict or "Low" in w.aurora_verdict
                      else "bold yellow")
        from rich.console import Group
        return Panel(Group(table, verdict), title="[bold]\U0001F31E SPACE WEATHER[/bold]", border_style="cyan")

    # ------------------------------------------------------------------ #
    # Earth Today
    # ------------------------------------------------------------------ #

    def _render_earth_photo(self) -> Panel:
        epic = self.hub.epic.value
        if epic is None:
            return _unavailable("EARTH TODAY", self.hub.epic.error)
        image_bytes = self.hub.get_epic_image_bytes()
        if image_bytes is None:
            body = Text("Fetching image…", style="dim")
        else:
            try:
                body = render_image_bytes(image_bytes, 70, 22)
            except Exception as exc:  # noqa: BLE001
                body = Text(f"Could not render image: {exc}", style="red")
        caption = Text(f"\n{epic.caption}  \u00b7  {epic.date} UTC", style="dim cyan")
        from rich.console import Group
        return Panel(Group(Align.center(body), caption),
                    title="[bold]\U0001F30D EARTH, RIGHT NOW (DSCOVR/EPIC)[/bold]", border_style="cyan")


def _unavailable(title: str, error) -> Panel:
    message = getattr(error, "message", None) or str(error) or "No data yet…"
    return Panel(Text(f"Unavailable: {message}", style="dim yellow"),
                title=f"[bold]{title}[/bold]", border_style="yellow")

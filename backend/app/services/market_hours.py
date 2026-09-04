from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.app.config import Instrument

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


"""
True if local_time falls inside one of the regular sessions (end time is exclusive)
"""
def _in_session(local_time: time, sessions: tuple[tuple[time, time], ...]) -> bool:
    return any(start <= local_time < end for start, end in sessions)


"""
The close time of the session that currently contains local_time, if any
"""
def _session_end(local_time: time, sessions: tuple[tuple[time, time], ...]) -> time | None:
    for start, end in sessions:
        if start <= local_time < end:
            return end
    return None


"""
The next weekday session open after local_now, including later the same day (e.g. after lunch)
"""
def _next_open_local(local_now: datetime, sessions: tuple[tuple[time, time], ...]) -> datetime:
    candidates: list[datetime] = []
    for day_offset in range(0, 8):
        day = (local_now + timedelta(days=day_offset)).date()
        if day.weekday() >= 5:
            continue
        for start, _end in sessions:
            candidate = datetime.combine(day, start, tzinfo=local_now.tzinfo)
            if candidate > local_now:
                candidates.append(candidate)
    return min(candidates) if candidates else local_now + timedelta(days=1)


"""
Return (is_open, short note) using weekday + regular hours only.
The note is either "Closes HH:MM" or "Opens HH:MM" / "Opens Mon HH:MM".
"""
def get_session(instrument: Instrument, now: datetime | None = None) -> tuple[bool, str]:
    now_utc = now or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    local = now_utc.astimezone(ZoneInfo(instrument.timezone))
    is_open = local.weekday() < 5 and _in_session(local.time(), instrument.sessions)

    if is_open:
        end = _session_end(local.time(), instrument.sessions)
        note = f"Closes {end.strftime('%H:%M')}" if end else "Open"
        return True, note

    nxt = _next_open_local(local, instrument.sessions)
    if nxt.date() == local.date():
        note = f"Opens {nxt.strftime('%H:%M')}"
    else:
        note = f"Opens {WEEKDAYS[nxt.weekday()]} {nxt.strftime('%H:%M')}"
    return False, note

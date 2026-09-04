from datetime import datetime
from zoneinfo import ZoneInfo

from backend.app.config import INDEX_BY_SYMBOL
from backend.app.services.market_hours import get_session


def _at(iso_local: str, timezone: str) -> datetime:
    naive = datetime.fromisoformat(iso_local)
    return naive.replace(tzinfo=ZoneInfo(timezone))


def test_us_open_during_regular_hours():
    now = _at("2026-09-03 10:00:00", "America/New_York")
    is_open, note = get_session(INDEX_BY_SYMBOL["^GSPC"], now)
    assert is_open is True
    assert note == "Closes 16:00"


def test_us_closed_after_hours():
    now = _at("2026-09-03 17:00:00", "America/New_York")
    is_open, note = get_session(INDEX_BY_SYMBOL["^GSPC"], now)
    assert is_open is False
    assert "Opens" in note


def test_us_closed_on_weekend():
    now = _at("2026-09-05 12:00:00", "America/New_York")
    is_open, note = get_session(INDEX_BY_SYMBOL["^IXIC"], now)
    assert is_open is False
    assert note.startswith("Opens Mon")


def test_hang_seng_closed_for_lunch():
    now = _at("2026-09-03 12:30:00", "Asia/Hong_Kong")
    is_open, note = get_session(INDEX_BY_SYMBOL["^HSI"], now)
    assert is_open is False
    assert note == "Opens 13:00"


def test_nikkei_open_afternoon_session():
    now = _at("2026-09-03 13:00:00", "Asia/Tokyo")
    is_open, note = get_session(INDEX_BY_SYMBOL["^N225"], now)
    assert is_open is True
    assert note == "Closes 15:00"

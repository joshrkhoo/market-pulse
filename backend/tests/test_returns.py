import pytest

from backend.app.services.yfinance_client import _daily_return_pct


def test_daily_return_pct():
    assert _daily_return_pct(102.0, 100.0) == pytest.approx(2.0)


def test_daily_return_pct_insufficient_data():
    assert _daily_return_pct(100.0, None) is None


def test_daily_return_pct_zero_previous_close():
    assert _daily_return_pct(10.0, 0.0) is None

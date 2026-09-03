import pytest

from backend.app.services.yfinance_client import _daily_return_pct


def test_daily_return_pct():
    import pandas as pd

    closes = pd.Series([100.0, 102.0])
    assert _daily_return_pct(closes) == pytest.approx(2.0)


def test_daily_return_pct_insufficient_data():
    import pandas as pd

    closes = pd.Series([100.0])
    assert _daily_return_pct(closes) is None


def test_daily_return_pct_zero_previous_close():
    import pandas as pd

    closes = pd.Series([0.0, 10.0])
    assert _daily_return_pct(closes) is None

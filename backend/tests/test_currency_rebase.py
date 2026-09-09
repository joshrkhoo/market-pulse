from datetime import datetime, timezone

import pandas as pd
import pytest

from backend.app.services.currency_convert import (
    align_fx_to_prices,
    convert_to_base,
    invert_fx_rate,
)
from backend.app.services.rebase import period_return_pct, rebase_to_100


def test_invert_fx_rate():
    assert invert_fx_rate(1.5) == pytest.approx(1 / 1.5)
    with pytest.raises(ValueError):
        invert_fx_rate(0)


def test_same_currency_fx_is_one():
    prices = pd.Series([100.0, 110.0], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
    fx = pd.Series([1.0, 1.0], index=prices.index)
    converted = convert_to_base(prices, fx)
    assert list(converted.values) == pytest.approx([100.0, 110.0])


def test_usd_to_aud_example_local_and_base_returns():
    """
    Stock: 100 USD → 110 USD  (+10% local)
    USD/AUD: 1.50 → 1.60
    AUD value: 150 → 176  (+17.33% base)
    Rebased AUD: 100 → 117.33
    """
    prices = pd.Series(
        [100.0, 110.0],
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )
    # 1 USD = X AUD
    fx = pd.Series(
        [1.50, 1.60],
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )

    converted = convert_to_base(prices, fx)
    assert list(converted.values) == pytest.approx([150.0, 176.0])

    local_ret = period_return_pct(prices)
    base_ret = period_return_pct(converted)
    assert local_ret == pytest.approx(10.0)
    assert base_ret == pytest.approx(17.3333, rel=1e-3)

    rebased = rebase_to_100(converted)
    assert float(rebased.iloc[0]) == pytest.approx(100.0)
    assert float(rebased.iloc[-1]) == pytest.approx(117.3333, rel=1e-3)


def test_fx_inversion_then_convert():
    prices = pd.Series([100.0, 110.0], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
    # Provider gives AUD per path wrong way: 1 AUD = X USD, we need 1 USD = X AUD
    audusd = pd.Series([0.6666667, 0.625], index=prices.index)
    usdaud = audusd.map(invert_fx_rate)
    converted = convert_to_base(prices, usdaud)
    assert list(converted.values) == pytest.approx([150.0, 176.0], rel=1e-3)


def test_missing_fx_date_uses_previous_rate():
    prices = pd.Series(
        [100.0, 105.0, 110.0],
        index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
    )
    # No FX print on 2024-01-03 (weekend/holiday style gap)
    fx = pd.Series(
        [1.50, 1.60],
        index=pd.to_datetime(["2024-01-02", "2024-01-04"]),
    )
    converted = convert_to_base(prices, fx)
    assert len(converted) == 3
    assert float(converted.iloc[1]) == pytest.approx(105.0 * 1.50)


def test_missing_values_never_filled_with_zero():
    prices = pd.Series(
        [100.0, None, 110.0],
        index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
    )
    fx = pd.Series([1.5, 1.5, 1.5], index=prices.index)
    converted = convert_to_base(prices, fx)
    assert 0.0 not in set(converted.values)
    assert len(converted) == 2


def test_rebase_starts_at_100():
    prices = pd.Series([50.0, 55.0, 60.0])
    rebased = rebase_to_100(prices)
    assert float(rebased.iloc[0]) == 100.0
    assert float(rebased.iloc[-1]) == pytest.approx(120.0)


def test_align_fx_empty_prices():
    aligned = align_fx_to_prices(pd.Series(dtype=float), pd.Series([1.5]))
    assert aligned.empty

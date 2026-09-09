"""
Tests for the compare endpoint's return perspective:
- "local": each asset rebased in its own currency (no FX applied)
- "base": FX convert into the base currency, then rebase
Plus the max-symbols cap on /api/markets/compare.
"""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.config import MAX_COMPARISON_SYMBOLS
from backend.app.main import app
from backend.app.services import comparison as comp


def _series(values, dates):
    return pd.Series(values, index=pd.to_datetime(dates))


def test_local_perspective_rebases_native_without_fx(monkeypatch):
    dates = ["2024-01-02", "2024-01-03"]
    natives = {
        "^GSPC": _series([100.0, 110.0], dates),  # +10% USD
        "^HSI": _series([200.0, 220.0], dates),   # +10% HKD
    }

    def fake_native(instrument, period):
        return natives[instrument.symbol]

    def fail_fx(*args, **kwargs):
        raise AssertionError("FX must not be fetched in the local perspective")

    monkeypatch.setattr(comp, "_native_close_series", fake_native)
    monkeypatch.setattr(comp, "fetch_fx_rate_series", fail_fx)

    resp = comp.build_comparison(
        period="1M", symbols=["^GSPC", "^HSI"], perspective="local"
    )

    assert resp.perspective == "local"
    for series in resp.series:
        assert series.error is None
        # No FX means no base-currency return in the local view
        assert series.base_return_pct is None
        assert series.local_return_pct == pytest.approx(10.0)
        # Every series starts at 100 in its own currency
        assert float(series.points[0].rebased) == pytest.approx(100.0)
        assert float(series.points[-1].rebased) == pytest.approx(110.0)


def test_base_perspective_applies_fx(monkeypatch):
    dates = ["2024-01-02", "2024-01-03"]

    def fake_native(instrument, period):
        return _series([100.0, 110.0], dates)  # +10% native

    def fake_fx(native, base, period):
        # 1 native = X base; different currencies only
        if native.upper() == base.upper():
            return pd.Series(dtype=float)
        return _series([1.50, 1.60], dates)

    monkeypatch.setattr(comp, "_native_close_series", fake_native)
    monkeypatch.setattr(comp, "fetch_fx_rate_series", fake_fx)

    resp = comp.build_comparison(
        period="1M", base_currency="AUD", symbols=["^GSPC"], perspective="base"
    )

    assert resp.perspective == "base"
    series = resp.series[0]
    assert series.local_return_pct == pytest.approx(10.0)
    assert series.base_return_pct == pytest.approx(17.3333, rel=1e-3)
    assert float(series.points[-1].rebased) == pytest.approx(117.3333, rel=1e-3)


def test_local_and_base_differ_for_foreign_asset(monkeypatch):
    dates = ["2024-01-02", "2024-01-03"]

    def fake_native(instrument, period):
        return _series([100.0, 110.0], dates)  # +10% native

    def fake_fx(native, base, period):
        if native.upper() == base.upper():
            return pd.Series(dtype=float)
        return _series([1.50, 1.60], dates)

    monkeypatch.setattr(comp, "_native_close_series", fake_native)
    monkeypatch.setattr(comp, "fetch_fx_rate_series", fake_fx)

    local = comp.build_comparison(period="1M", symbols=["^HSI"], perspective="local")
    base = comp.build_comparison(
        period="1M", base_currency="AUD", symbols=["^HSI"], perspective="base"
    )

    assert local.series[0].local_return_pct == pytest.approx(10.0)
    assert base.series[0].base_return_pct == pytest.approx(17.3333, rel=1e-3)


def test_compare_rejects_too_many_symbols():
    client = TestClient(app)
    # Duplicates are known symbols, so this trips the cap (not the unknown-symbol check)
    symbols = ",".join(["^GSPC"] * (MAX_COMPARISON_SYMBOLS + 1))
    response = client.get("/api/markets/compare", params={"symbols": symbols})
    assert response.status_code == 400
    assert str(MAX_COMPARISON_SYMBOLS) in response.json()["detail"]


def test_compare_rejects_unknown_perspective():
    client = TestClient(app)
    response = client.get("/api/markets/compare", params={"perspective": "nonsense"})
    assert response.status_code == 400

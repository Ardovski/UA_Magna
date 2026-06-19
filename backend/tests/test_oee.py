"""`app.core.oee.recompute_oee` birim testleri."""

from __future__ import annotations

import pytest
from app.core.oee import recompute_oee


def test_basic_formula() -> None:
    # A = 90/(90+10)=90%, P=95, Q=(100-1)/100=99% → 0.9*95*0.99 = 84.645
    oee = recompute_oee(
        run_time=90, unplanned_down=10, performance=95, produced_qty=100, scrap_qty=1
    )
    assert oee == pytest.approx(0.90 * 95 * 99 / 100, rel=1e-6)


def test_performance_capped_at_100() -> None:
    # P=141.87 (>100) → 100'e clamp; A=100, Q=100 → OEE=100, garbage değil
    oee = recompute_oee(
        run_time=10, unplanned_down=0, performance=141.87, produced_qty=10, scrap_qty=0
    )
    assert oee == pytest.approx(100.0)


def test_zero_production_is_zero_oee() -> None:
    # Makine çalıştı ama üretmedi → gerçek %0 verimlilik
    assert (
        recompute_oee(run_time=8, unplanned_down=2, performance=90, produced_qty=0, scrap_qty=0)
        == 0.0
    )


def test_totally_idle_is_none() -> None:
    # Çalışma + plansız duruş = 0 → makine aktif değil → ortalama dışı
    assert (
        recompute_oee(run_time=0, unplanned_down=0, performance=90, produced_qty=0, scrap_qty=0)
        is None
    )


def test_missing_performance_is_none() -> None:
    assert (
        recompute_oee(run_time=8, unplanned_down=2, performance=None, produced_qty=10, scrap_qty=0)
        is None
    )


def test_scrap_exceeds_produced_clamped_to_zero() -> None:
    # Q negatif olur → 0'a clamp → OEE 0 (tutarsız kayıt)
    oee = recompute_oee(
        run_time=10, unplanned_down=0, performance=100, produced_qty=10, scrap_qty=15
    )
    assert oee == 0.0

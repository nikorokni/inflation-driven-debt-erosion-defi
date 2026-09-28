"""Independent accounting examples for mutually exclusive settlement paths."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from borrower_cashflows import CostAssumptions, liquidation_cashflow, survivor_cashflow


ZERO = CostAssumptions(0, 0, 0)


def test_survivor_repay_and_receive_collateral_back():
    result = survivor_cashflow(100, 1, 1, 1, 0, ZERO)
    assert np.isclose(result["debt_service_usd"], 100)
    assert np.isclose(result["net_benefit_usd"], 0)
    assert np.isclose(survivor_cashflow(100, 1, 2, 1, 0, ZERO)["net_benefit_usd"], 50)


def test_liquidated_with_surplus_pays_debt_penalty_only_from_surplus():
    outcome = liquidation_cashflow(100, 1, 1, 0.5, 180, 0, 0.10, assumptions=ZERO)
    assert np.isclose(outcome["debt_recovered_usd"], 100)
    assert np.isclose(outcome["penalty_collected_usd"], 10)
    assert np.isclose(outcome["borrower_residual_usd"], 70)
    assert np.isclose(outcome["bad_debt_usd"], 0)
    assert np.isclose(outcome["net_benefit_usd"], -10)
    assert np.isclose(outcome["debt_recovered_usd"] + outcome["penalty_collected_usd"]
                      + outcome["borrower_residual_usd"], outcome["sale_proceeds_usd"])


def test_liquidated_with_shortfall_has_no_second_horizon_repayment():
    outcome = liquidation_cashflow(100, 1, 1, 0.5, 60, 0, 0.13, assumptions=ZERO)
    assert np.isclose(outcome["debt_recovered_usd"], 60)
    assert np.isclose(outcome["bad_debt_usd"], 40)
    assert np.isclose(outcome["penalty_collected_usd"], 0)
    assert np.isclose(outcome["net_benefit_usd"], 40)
    assert np.isclose(outcome["debt_recovered_usd"] + outcome["bad_debt_usd"],
                      outcome["debt_at_liquidation_usd"])


def test_haircut_is_not_counted_as_an_extra_borrower_repayment():
    outcome = liquidation_cashflow(100, 1, 1, 1, 120, 0, 0.13,
                                   auction_haircut_fraction=0.25, assumptions=ZERO)
    assert np.isclose(outcome["sale_proceeds_usd"], 90)
    assert np.isclose(outcome["bad_debt_usd"], 10)
    assert np.isclose(outcome["net_benefit_usd"], -20)


def test_fee_conversion_and_gas_timing_are_explicit():
    costs = CostAssumptions(0.01, 0.02, 40)
    paid = survivor_cashflow(100, 1, 1, 1, 0, costs)
    seized = liquidation_cashflow(100, 1, 1, 1, 200, 0, 0.1, assumptions=costs)
    assert np.isclose(paid["net_benefit_usd"], -45)
    assert np.isclose(seized["net_benefit_usd"], -33)
    assert "exit_conversion_usd" not in seized
    assert "closing_gas_usd" not in seized


def test_capped_penalty_and_vectorised_ledger():
    out = liquidation_cashflow([100, 100], 1, 1, [0.5, 0.5], [105, 90], 0, 0.13,
                               assumptions=ZERO)
    np.testing.assert_allclose(out["penalty_collected_usd"], [5, 0])
    np.testing.assert_allclose(out["borrower_residual_usd"], [0, 0])
    np.testing.assert_allclose(out["bad_debt_usd"], [0, 10])


def test_invalid_debt_or_collateral_inputs_rejected():
    try:
        liquidation_cashflow(100, 1, 0, 1, 200, 0.2, 0.13)
    except ValueError:
        pass
    else:
        raise AssertionError("zero FX must be rejected")


if __name__ == "__main__":
    for name in sorted(n for n in globals() if n.startswith("test_")):
        globals()[name]()
        print(f"{name}: ok")

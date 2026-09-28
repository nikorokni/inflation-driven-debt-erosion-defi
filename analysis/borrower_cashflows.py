"""Conditional borrower and protocol accounting for a hypothetical LCU vault.

The two close-out routes are mutually exclusive. No liquidation output contains a
separate voluntary repayment at the originally planned horizon.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CostAssumptions:
    # All percentages are illustrative, not estimates for an operating LCU vault.
    protocol_fee_fraction: float = 0.005
    conversion_fraction_each_way: float = 0.003
    gas_usd_round_trip: float = 40.0

    @property
    def opening_gas_usd(self) -> float:
        return self.gas_usd_round_trip / 2.0

    @property
    def voluntary_closing_gas_usd(self) -> float:
        return self.gas_usd_round_trip / 2.0


def _array(value: object) -> np.ndarray:
    return np.asarray(value, dtype=float)


def accrued_debt_usd(
    principal_usd: object,
    fx_start_lcu_per_usd: object,
    fx_close_lcu_per_usd: object,
    years: object,
    annual_effective_rate: float,
) -> np.ndarray:
    """Local principal and interest converted to USD at the settlement date."""
    p, e0, et, t = map(
        _array,
        (principal_usd, fx_start_lcu_per_usd, fx_close_lcu_per_usd, years),
    )
    if np.any(p <= 0) or np.any(e0 <= 0) or np.any(et <= 0) or np.any(t < 0):
        raise ValueError("Principal and FX must be positive; duration cannot be negative")
    if annual_effective_rate <= -1:
        raise ValueError("The effective annual rate must exceed -100%")
    return p * e0 / et * (1.0 + annual_effective_rate) ** t


def survivor_cashflow(
    principal_usd: object,
    fx_start_lcu_per_usd: object,
    fx_close_lcu_per_usd: object,
    years: object,
    annual_effective_rate: float,
    assumptions: CostAssumptions = CostAssumptions(),
) -> dict[str, np.ndarray]:
    """Voluntary full repayment: collateral is returned, so no collateral cost."""
    p = _array(principal_usd)
    debt = accrued_debt_usd(p, fx_start_lcu_per_usd, fx_close_lcu_per_usd, years, annual_effective_rate)
    fee = assumptions.protocol_fee_fraction * p
    entry = assumptions.conversion_fraction_each_way * p
    exit_cost = assumptions.conversion_fraction_each_way * debt
    opening_gas = assumptions.opening_gas_usd
    closing_gas = assumptions.voluntary_closing_gas_usd
    benefit = p - fee - entry - opening_gas - debt - exit_cost - closing_gas
    return {
        "debt_service_usd": debt,
        "origination_fee_usd": fee,
        "entry_conversion_usd": entry,
        "exit_conversion_usd": exit_cost,
        "opening_gas_usd": np.broadcast_to(opening_gas, debt.shape),
        "closing_gas_usd": np.broadcast_to(closing_gas, debt.shape),
        "net_benefit_usd": benefit,
    }


def liquidation_cashflow(
    principal_usd: object,
    fx_start_lcu_per_usd: object,
    fx_liquidation_lcu_per_usd: object,
    years_to_liquidation: object,
    collateral_marked_usd: object,
    annual_effective_rate: float,
    liquidation_penalty_fraction: float,
    auction_haircut_fraction: float = 0.0,
    assumptions: CostAssumptions = CostAssumptions(),
) -> dict[str, np.ndarray]:
    """Immediate full collateral sale at tau; the stylised debt is nonrecourse.

    The reported benefit is the incremental terminal USD value of draw proceeds
    relative to keeping the same collateral without borrowing. It is not a
    realised investment return: investment of proceeds, taxes and cash timing
    are deliberately absent. Any shortfall is a lender/issuer asset write-down.
    """
    p = _array(principal_usd)
    marked = _array(collateral_marked_usd)
    if np.any(marked < 0) or not (0 <= auction_haircut_fraction <= 1):
        raise ValueError("Collateral must be nonnegative; haircut must be in [0, 1]")
    if liquidation_penalty_fraction < 0:
        raise ValueError("Penalty must be nonnegative")
    debt = accrued_debt_usd(p, fx_start_lcu_per_usd, fx_liquidation_lcu_per_usd, years_to_liquidation, annual_effective_rate)
    proceeds = marked * (1.0 - auction_haircut_fraction)
    recovered = np.minimum(proceeds, debt)
    shortfall = debt - recovered
    surplus = np.maximum(proceeds - debt, 0.0)
    penalty = np.minimum(liquidation_penalty_fraction * debt, surplus)
    residual = surplus - penalty
    fee = assumptions.protocol_fee_fraction * p
    entry = assumptions.conversion_fraction_each_way * p
    benefit = p - fee - entry - assumptions.opening_gas_usd - marked + residual
    return {
        "debt_at_liquidation_usd": debt,
        "collateral_marked_usd": marked,
        "sale_proceeds_usd": proceeds,
        "debt_recovered_usd": recovered,
        "penalty_collected_usd": penalty,
        "borrower_residual_usd": residual,
        "bad_debt_usd": shortfall,
        "origination_fee_usd": fee,
        "entry_conversion_usd": entry,
        "opening_gas_usd": np.broadcast_to(assumptions.opening_gas_usd, debt.shape),
        "net_benefit_usd": benefit,
    }

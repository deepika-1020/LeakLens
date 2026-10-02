import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import sys

# Ensure local imports work cleanly
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import get_unified_orders, FAILED_DELIVERY_STATUSES

# ==============================================================================
# LEAKLENS - REVENUE TREND & PERIOD-OVER-PERIOD ANALYZER
# Role: Data Analytics & AI
# ==============================================================================

def get_monthly_metrics(unified_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate deterministic monthly business and leakage metrics across all periods.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    monthly_records = []

    for ym, group in unified_df.groupby("year_month"):
        month_label = group["month_name"].iloc[0]
        order_vol = len(group)
        gross_rev = group["gross_revenue"].sum()
        discount_amt = group["discount_amount"].sum()
        billed_rev = group["total_amount"].sum()
        aov = billed_rev / order_vol if order_vol > 0 else 0.0

        # Refund leakage within this order cohort
        refund_amt = group["refund_amount"].sum()
        refunded_orders = (group["refund_amount"] > 0).sum()

        # Delivery failure value (orders with Failed/Cancelled/Returned status)
        failed_delivery_mask = group["delivery_status"].isin(FAILED_DELIVERY_STATUSES)
        delivery_failure_val = group.loc[failed_delivery_mask, "total_amount"].sum()
        failed_delivery_orders = failed_delivery_mask.sum()

        # Net Realized Revenue
        net_rev = group["net_realized_revenue"].sum()

        # Controlled high discount leakage (discounts >= 35%)
        high_disc_mask = group["discount"] >= 35.0
        high_discount_val = group.loc[high_disc_mask, "discount_amount"].sum()
        high_discount_orders = high_disc_mask.sum()

        monthly_records.append({
            "year_month": ym,
            "month_label": month_label,
            "order_volume": int(order_vol),
            "gross_revenue": round(float(gross_rev), 2),
            "discount_amount": round(float(discount_amt), 2),
            "billed_revenue": round(float(billed_rev), 2),
            "aov": round(float(aov), 2),
            "refund_amount": round(float(refund_amt), 2),
            "refunded_orders": int(refunded_orders),
            "delivery_failure_value": round(float(delivery_failure_val), 2),
            "failed_delivery_orders": int(failed_delivery_orders),
            "high_discount_value": round(float(high_discount_val), 2),
            "high_discount_orders": int(high_discount_orders),
            "net_realized_revenue": round(float(net_rev), 2)
        })

    metrics_df = pd.DataFrame(monthly_records).sort_values("year_month").reset_index(drop=True)
    return metrics_df


def compare_periods(
    unified_df: Optional[pd.DataFrame] = None,
    current_period: Optional[str] = None,
    previous_period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform rigorous Period-over-Period (PoP) comparison.
    If periods are not specified, defaults to comparing the latest two available months.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    monthly_df = get_monthly_metrics(unified_df)
    available_periods = monthly_df["year_month"].tolist()

    if len(available_periods) < 2:
        raise ValueError("At least two distinct monthly periods are required for trend analysis.")

    # Default to the most recent two periods (e.g. 2026-08 vs 2026-09)
    if not current_period:
        current_period = available_periods[-1]
    if not previous_period:
        # Find index of current_period
        if current_period in available_periods:
            curr_idx = available_periods.index(current_period)
            previous_period = available_periods[max(0, curr_idx - 1)]
        else:
            previous_period = available_periods[-2]

    curr_row = monthly_df[monthly_df["year_month"] == current_period]
    prev_row = monthly_df[monthly_df["year_month"] == previous_period]

    if curr_row.empty or prev_row.empty:
        raise ValueError(f"One or both periods not found. Current: {current_period}, Previous: {previous_period}. Available: {available_periods}")

    curr = curr_row.iloc[0].to_dict()
    prev = prev_row.iloc[0].to_dict()

    # Calculate absolute & percentage changes
    net_rev_prev = prev["net_realized_revenue"]
    net_rev_curr = curr["net_realized_revenue"]
    net_rev_change = round(net_rev_curr - net_rev_prev, 2)
    net_rev_pct = round((net_rev_change / net_rev_prev) * 100.0, 2) if net_rev_prev > 0 else 0.0

    billed_prev = prev["billed_revenue"]
    billed_curr = curr["billed_revenue"]
    billed_change = round(billed_curr - billed_prev, 2)
    billed_pct = round((billed_change / billed_prev) * 100.0, 2) if billed_prev > 0 else 0.0

    vol_change = curr["order_volume"] - prev["order_volume"]
    vol_pct = round((vol_change / prev["order_volume"]) * 100.0, 2) if prev["order_volume"] > 0 else 0.0

    aov_change = round(curr["aov"] - prev["aov"], 2)
    aov_pct = round((aov_change / prev["aov"]) * 100.0, 2) if prev["aov"] > 0 else 0.0

    refund_change = round(curr["refund_amount"] - prev["refund_amount"], 2)
    refund_pct = round((refund_change / prev["refund_amount"]) * 100.0, 2) if prev["refund_amount"] > 0 else 0.0

    delivery_leak_change = round(curr["delivery_failure_value"] - prev["delivery_failure_value"], 2)
    delivery_leak_pct = round((delivery_leak_change / prev["delivery_failure_value"]) * 100.0, 2) if prev["delivery_failure_value"] > 0 else 0.0

    discount_change = round(curr["discount_amount"] - prev["discount_amount"], 2)

    # Determine business direction
    if net_rev_change < -500:
        direction = "DECLINE"
    elif net_rev_change > 500:
        direction = "GROWTH"
    else:
        direction = "STABLE"

    # Waterfall decomposition of revenue difference
    waterfall = [
        {"step": f"Baseline Net Revenue ({prev['month_label']})", "amount": net_rev_prev, "type": "baseline"},
        {"step": "Order Volume Impact", "amount": round(vol_change * prev["aov"], 2), "type": "driver"},
        {"step": "AOV & Price Impact", "amount": round(curr["order_volume"] * aov_change, 2), "type": "driver"},
        {"step": "Incremental Delivery Failures", "amount": round(-delivery_leak_change, 2), "type": "leakage"},
        {"step": "Incremental Refunds", "amount": round(-refund_change, 2), "type": "leakage"},
        {"step": f"Current Net Revenue ({curr['month_label']})", "amount": net_rev_curr, "type": "total"}
    ]

    return {
        "current_period": current_period,
        "current_label": curr["month_label"],
        "previous_period": previous_period,
        "previous_label": prev["month_label"],
        "direction": direction,
        "net_revenue": {
            "previous": net_rev_prev,
            "current": net_rev_curr,
            "absolute_change": net_rev_change,
            "percentage_change": net_rev_pct
        },
        "billed_revenue": {
            "previous": billed_prev,
            "current": billed_curr,
            "absolute_change": billed_change,
            "percentage_change": billed_pct
        },
        "order_volume": {
            "previous": prev["order_volume"],
            "current": curr["order_volume"],
            "absolute_change": vol_change,
            "percentage_change": vol_pct
        },
        "aov": {
            "previous": prev["aov"],
            "current": curr["aov"],
            "absolute_change": aov_change,
            "percentage_change": aov_pct
        },
        "refund_leakage": {
            "previous": prev["refund_amount"],
            "current": curr["refund_amount"],
            "absolute_change": refund_change,
            "percentage_change": refund_pct,
            "orders_previous": prev["refunded_orders"],
            "orders_current": curr["refunded_orders"]
        },
        "delivery_leakage": {
            "previous": prev["delivery_failure_value"],
            "current": curr["delivery_failure_value"],
            "absolute_change": delivery_leak_change,
            "percentage_change": delivery_leak_pct,
            "orders_previous": prev["failed_delivery_orders"],
            "orders_current": curr["failed_delivery_orders"]
        },
        "discount_impact": {
            "previous": prev["discount_amount"],
            "current": curr["discount_amount"],
            "absolute_change": discount_change
        },
        "waterfall": waterfall,
        "all_monthly_metrics": monthly_df.to_dict(orient="records")
    }

import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import get_unified_orders, FAILED_DELIVERY_STATUSES
from trend_analyzer import compare_periods, get_monthly_metrics

# ==============================================================================
# LEAKLENS - REVENUE DECLINE ROOT-CAUSE INVESTIGATOR
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Deterministic Driver Decomposition)
# ==============================================================================

def investigate_revenue_decline(
    unified_df: Optional[pd.DataFrame] = None,
    current_period: Optional[str] = None,
    previous_period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deterministically investigate the drivers of Month-over-Month revenue decline.
    Ranks contributors strictly using calculated values without unverified causal claims.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    # Step 1 & 2: Calculate Period Comparison
    comparison = compare_periods(unified_df, current_period, previous_period)
    curr_period = comparison["current_period"]
    prev_period = comparison["previous_period"]
    curr_label = comparison["current_label"]
    prev_label = comparison["previous_label"]
    net_rev_info = comparison["net_revenue"]

    # Step 3: Check whether revenue genuinely declined
    if comparison["direction"] != "DECLINE":
        return {
            "status": "NO_DECLINE",
            "message": f"The selected period ({curr_label}) did not show a net revenue decline compared to {prev_label}.",
            "net_revenue_change": net_rev_info["absolute_change"],
            "percentage_change": net_rev_info["percentage_change"],
            "current_period": curr_period,
            "previous_period": prev_period,
            "current_label": curr_label,
            "previous_label": prev_label,
            "comparison": comparison,
            "drivers": [],
            "recommendation": "Maintain standard operational monitoring as net realized revenue remains healthy or growing."
        }

    # Step 4: Investigate Potential Drivers
    curr_df = unified_df[unified_df["year_month"] == curr_period].copy()
    prev_df = unified_df[unified_df["year_month"] == prev_period].copy()

    # Driver 1: Incremental Delivery Failure Leakage
    curr_deliv_leak = comparison["delivery_leakage"]["current"]
    prev_deliv_leak = comparison["delivery_leakage"]["previous"]
    deliv_leak_impact = round(max(0.0, curr_deliv_leak - prev_deliv_leak), 2)

    # Driver 2: Incremental Refund Leakage
    curr_refund_leak = comparison["refund_leakage"]["current"]
    prev_refund_leak = comparison["refund_leakage"]["previous"]
    refund_leak_impact = round(max(0.0, curr_refund_leak - prev_refund_leak), 2)

    # Driver 3: Order Volume Drop
    curr_vol = comparison["order_volume"]["current"]
    prev_vol = comparison["order_volume"]["previous"]
    prev_aov = comparison["aov"]["previous"]
    volume_drop_impact = round(max(0.0, (prev_vol - curr_vol) * prev_aov), 2) if curr_vol < prev_vol else 0.0

    # Driver 4: AOV Compression
    curr_aov = comparison["aov"]["current"]
    aov_drop_impact = round(max(0.0, curr_vol * (prev_aov - curr_aov)), 2) if curr_aov < prev_aov else 0.0

    # Driver 5: Incremental Discount Leakage
    curr_disc = comparison["discount_impact"]["current"]
    prev_disc = comparison["discount_impact"]["previous"]
    discount_leak_impact = round(max(0.0, curr_disc - prev_disc), 2)

    # Total observed adverse variance
    total_decline_abs = abs(net_rev_info["absolute_change"])

    # Step 5: Rank contributing drivers by adverse financial impact
    drivers = [
        {
            "name": "Delivery Failures & Cancellations",
            "type": "Logistics & Fulfillment",
            "financial_impact": deliv_leak_impact,
            "share_of_decline": round((deliv_leak_impact / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0,
            "description": f"Incremental delivery losses of ₹{deliv_leak_impact:,.2f} ({comparison['delivery_leakage']['percentage_change']:+.1f}% vs {prev_label})."
        },
        {
            "name": "Customer Refund Spike",
            "type": "Product Quality & Returns",
            "financial_impact": refund_leak_impact,
            "share_of_decline": round((refund_leak_impact / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0,
            "description": f"Incremental refunds of ₹{refund_leak_impact:,.2f} ({comparison['refund_leakage']['percentage_change']:+.1f}% vs {prev_label})."
        },
        {
            "name": "Order Volume Reduction",
            "type": "Demand & Traffic",
            "financial_impact": volume_drop_impact,
            "share_of_decline": round((volume_drop_impact / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0,
            "description": f"Order count shifted from {prev_vol} to {curr_vol} orders ({comparison['order_volume']['percentage_change']:+.1f}%)."
        },
        {
            "name": "Average Order Value (AOV) Compression",
            "type": "Pricing & Basket Size",
            "financial_impact": aov_drop_impact,
            "share_of_decline": round((aov_drop_impact / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0,
            "description": f"AOV changed from ₹{prev_aov:,.2f} to ₹{curr_aov:,.2f} ({comparison['aov']['percentage_change']:+.1f}%)."
        },
        {
            "name": "Excess Promotional Discounts",
            "type": "Pricing Policy",
            "financial_impact": discount_leak_impact,
            "share_of_decline": round((discount_leak_impact / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0,
            "description": f"Discounts expanded by ₹{discount_leak_impact:,.2f} in {curr_label}."
        }
    ]

    # Sort drivers strictly descending by financial impact
    drivers = sorted(drivers, key=lambda d: d["financial_impact"], reverse=True)
    top_driver = drivers[0]

    # Deep Slice: Category Breakdown in Current Month
    cat_summary = curr_df.groupby("category").agg(
        order_count=("order_id", "count"),
        gross_revenue=("gross_revenue", "sum"),
        total_billed=("total_amount", "sum"),
        refund_amount=("refund_amount", "sum"),
        failed_delivery_val=("total_amount", lambda x: x[curr_df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum()),
        net_revenue=("net_realized_revenue", "sum")
    ).reset_index()

    # Category Net Decline vs Previous Month
    prev_cat_net = prev_df.groupby("category")["net_realized_revenue"].sum()
    cat_summary["prev_net_revenue"] = cat_summary["category"].map(prev_cat_net).fillna(0.0)
    cat_summary["net_decline"] = cat_summary["prev_net_revenue"] - cat_summary["net_revenue"]
    cat_summary = cat_summary.sort_values("net_decline", ascending=False).reset_index(drop=True)

    top_category = cat_summary.iloc[0]["category"]
    top_cat_decline = round(float(cat_summary.iloc[0]["net_decline"]), 2)
    top_cat_share = round((top_cat_decline / total_decline_abs) * 100.0, 1) if total_decline_abs > 0 else 0.0

    # Deep Slice: Location Breakdown of Delivery Failures in Current Month
    curr_failed = curr_df[curr_df["delivery_status"].isin(FAILED_DELIVERY_STATUSES)]
    loc_summary = curr_failed.groupby("location").agg(
        failed_orders=("order_id", "count"),
        failed_revenue=("total_amount", "sum")
    ).sort_values("failed_revenue", ascending=False).reset_index()

    top_location = loc_summary.iloc[0]["location"] if not loc_summary.empty else "N/A"
    top_loc_impact = round(float(loc_summary.iloc[0]["failed_revenue"]), 2) if not loc_summary.empty else 0.0

    # Deep Slice: Customer Segment Breakdown
    seg_summary = curr_df.groupby("customer_segment").agg(
        net_revenue=("net_realized_revenue", "sum"),
        refund_amount=("refund_amount", "sum"),
        failed_delivery_val=("total_amount", lambda x: x[curr_df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum())
    ).reset_index()
    seg_summary["total_leakage"] = seg_summary["refund_amount"] + seg_summary["failed_delivery_val"]
    seg_summary = seg_summary.sort_values("total_leakage", ascending=False).reset_index(drop=True)

    top_segment = seg_summary.iloc[0]["customer_segment"] if not seg_summary.empty else "N/A"
    top_seg_leakage = round(float(seg_summary.iloc[0]["total_leakage"]), 2) if not seg_summary.empty else 0.0

    # Refund Reason Breakdown for the Top Category
    top_cat_refunds = curr_df[(curr_df["category"] == top_category) & (curr_df["refund_amount"] > 0)]
    reason_summary = top_cat_refunds.groupby("refund_reason")["refund_amount"].sum().sort_values(ascending=False).reset_index()
    top_refund_reason = reason_summary.iloc[0]["refund_reason"] if not reason_summary.empty else "Customer Request"

    # Step 6: Identify Strongest Supporting Evidence
    # Target records: Failed deliveries or refunds in top category for current period
    evidence_records = curr_df[
        (curr_df["category"] == top_category) & 
        (curr_df["delivery_status"].isin(FAILED_DELIVERY_STATUSES) | (curr_df["refund_amount"] > 0))
    ][[
        "order_id", "customer_id", "order_date", "category", 
        "location", "customer_segment", "total_amount", 
        "delivery_status", "refund_amount", "refund_reason"
    ]].sort_values(by=["refund_amount", "total_amount"], ascending=False).reset_index(drop=True)

    # Step 7: Generate Fact-Based Actionable Recommendation
    recommendation = (
        f"1. Logistics Audit: Immediately inspect 3PL courier operations in {top_location} where delivery failures accounted for ₹{top_loc_impact:,.2f} in revenue loss.\n"
        f"2. Product Quality & Packaging: Investigate {top_category} fulfillment processes, prioritizing cases cited as '{top_refund_reason}' to arrest ₹{refund_leak_impact:,.2f} in incremental refunds.\n"
        f"3. Policy Controls: Review {top_segment} customer order handling to protect enterprise retention."
    )

    return {
        "status": "DECLINE_DETECTED",
        "current_period": curr_period,
        "previous_period": prev_period,
        "current_label": curr_label,
        "previous_label": prev_label,
        "net_revenue_change": net_rev_info["absolute_change"],
        "percentage_change": net_rev_info["percentage_change"],
        "comparison": comparison,
        "ranked_drivers": drivers,
        "primary_driver": top_driver,
        "root_cause_dimensions": {
            "top_category": {
                "name": top_category,
                "net_decline": top_cat_decline,
                "share_of_decline": top_cat_share
            },
            "top_location": {
                "name": top_location,
                "failed_delivery_impact": top_loc_impact
            },
            "top_segment": {
                "name": top_segment,
                "leakage_impact": top_seg_leakage
            },
            "top_refund_reason": top_refund_reason
        },
        "evidence_trace": {
            "source_datasets": ["orders.csv", "deliveries.csv", "refunds.csv", "customers.csv"],
            "filter_applied": f"year_month = '{curr_period}' AND category = '{top_category}' AND (delivery_status IN ('Cancelled', 'Failed', 'Returned') OR refund_amount > 0)",
            "calculation_formula": f"Net Revenue = Billed Sales - Failed Deliveries - Refund Amount",
            "sample_record_count": len(evidence_records),
            "evidence_dataframe": evidence_records
        },
        "recommendation": recommendation,
        "requires_human_approval": True
    }

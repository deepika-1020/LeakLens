import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import load_data, get_unified_orders, FAILED_DELIVERY_STATUSES

# ==============================================================================
# LEAKLENS - EVIDENCE TRACE ENGINE
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Evidence Traceability & Record-Level Proof)
# ==============================================================================

def refund_evidence(
    unified_df: Optional[pd.DataFrame] = None,
    category: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate verifiable evidence trace for refund leakage.
    Traces aggregations directly back to underlying order and refund records.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    filtered = unified_df[unified_df["refund_amount"] > 0].copy()

    filter_desc = ["refund_amount > 0"]

    if period:
        filtered = filtered[filtered["year_month"] == period]
        filter_desc.append(f"year_month = '{period}'")

    if category:
        filtered = filtered[filtered["category"] == category]
        filter_desc.append(f"category = '{category}'")

    total_refund = filtered["refund_amount"].sum()

    # Category breakdown
    cat_summary = (
        filtered.groupby("category")
        .agg(
            refund_amount=("refund_amount", "sum"),
            order_count=("order_id", "nunique")
        )
        .sort_values("refund_amount", ascending=False)
    )

    top_cat = cat_summary.index[0] if not cat_summary.empty else "N/A"
    top_cat_impact = float(cat_summary.iloc[0]["refund_amount"]) if not cat_summary.empty else 0.0
    top_cat_orders = int(cat_summary.iloc[0]["order_count"]) if not cat_summary.empty else 0
    cat_share = (top_cat_impact / total_refund * 100.0) if total_refund > 0 else 0.0

    # Reason breakdown
    reason_summary = (
        filtered.groupby("refund_reason")
        .agg(refund_amount=("refund_amount", "sum"))
        .sort_values("refund_amount", ascending=False)
    )
    top_reason = reason_summary.index[0] if not reason_summary.empty else "N/A"
    top_reason_impact = float(reason_summary.iloc[0]["refund_amount"]) if not reason_summary.empty else 0.0

    # Evidence records: top records for the primary category
    evidence_records = filtered[filtered["category"] == top_cat][[
        "order_id", "customer_id", "order_date", "category", 
        "location", "customer_segment", "total_amount", 
        "refund_amount", "refund_reason"
    ]].sort_values(by="refund_amount", ascending=False).reset_index(drop=True)

    filter_str = " AND ".join(filter_desc)

    return {
        "decision_type": "Refund Leakage",
        "sources": ["refunds.csv", "orders.csv", "customers.csv"],
        "filter": filter_str,
        "affected_orders": len(filtered),
        "financial_impact": round(float(total_refund), 2),
        "primary_category": top_cat,
        "primary_category_impact": round(top_cat_impact, 2),
        "primary_category_orders": top_cat_orders,
        "category_share": round(cat_share, 2),
        "primary_reason": top_reason,
        "primary_reason_impact": round(top_reason_impact, 2),
        "calculation": f"₹{top_cat_impact:,.2f} (Category Total) / ₹{total_refund:,.2f} (Total Refunds) × 100",
        "conclusion": f"{top_cat} is the largest observed contributor to refund leakage, primarily driven by '{top_reason}'.",
        "recommendation": f"Initiate vendor packaging and QC audit on {top_cat} product lines, focusing on '{top_reason}' cases.",
        "evidence_records": evidence_records,
        "human_approval": "PENDING"
    }


def delivery_evidence(
    unified_df: Optional[pd.DataFrame] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate verifiable evidence trace for delivery failure and cancellation risk.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    filtered = unified_df[unified_df["delivery_status"].isin(FAILED_DELIVERY_STATUSES)].copy()
    filter_desc = ["delivery_status IN ('Cancelled', 'Failed', 'Returned')"]

    if period:
        filtered = filtered[filtered["year_month"] == period]
        filter_desc.append(f"year_month = '{period}'")

    if category:
        filtered = filtered[filtered["category"] == category]
        filter_desc.append(f"category = '{category}'")

    if location:
        filtered = filtered[filtered["location"] == location]
        filter_desc.append(f"location = '{location}'")

    total_risk = filtered["total_amount"].sum()

    # Category breakdown
    cat_summary = (
        filtered.groupby("category")
        .agg(
            revenue_at_risk=("total_amount", "sum"),
            order_count=("order_id", "nunique")
        )
        .sort_values("revenue_at_risk", ascending=False)
    )

    top_cat = cat_summary.index[0] if not cat_summary.empty else "N/A"
    top_cat_risk = float(cat_summary.iloc[0]["revenue_at_risk"]) if not cat_summary.empty else 0.0
    top_cat_orders = int(cat_summary.iloc[0]["order_count"]) if not cat_summary.empty else 0
    cat_share = (top_cat_risk / total_risk * 100.0) if total_risk > 0 else 0.0

    # Location breakdown
    loc_summary = (
        filtered.groupby("location")
        .agg(revenue_at_risk=("total_amount", "sum"))
        .sort_values("revenue_at_risk", ascending=False)
    )
    top_loc = loc_summary.index[0] if not loc_summary.empty else "N/A"
    top_loc_impact = float(loc_summary.iloc[0]["revenue_at_risk"]) if not loc_summary.empty else 0.0

    # Evidence records: top records for primary category
    evidence_records = filtered[filtered["category"] == top_cat][[
        "order_id", "customer_id", "order_date", "category", 
        "location", "delivery_status", "total_amount"
    ]].sort_values(by="total_amount", ascending=False).reset_index(drop=True)

    filter_str = " AND ".join(filter_desc)

    return {
        "decision_type": "Delivery Leakage",
        "sources": ["deliveries.csv", "orders.csv", "customers.csv"],
        "filter": filter_str,
        "affected_orders": len(filtered),
        "financial_impact": round(float(total_risk), 2),
        "primary_category": top_cat,
        "primary_category_impact": round(top_cat_risk, 2),
        "primary_category_orders": top_cat_orders,
        "category_share": round(cat_share, 2),
        "primary_location": top_loc,
        "primary_location_impact": round(top_loc_impact, 2),
        "calculation": f"₹{top_cat_risk:,.2f} (Category Total) / ₹{total_risk:,.2f} (Total Delivery Risk) × 100",
        "conclusion": f"{top_cat} orders represent {cat_share:.1f}% of total delivery failure revenue risk, with high concentration in {top_loc}.",
        "recommendation": f"Audit regional logistics routing and SLA enforcement in {top_loc} for high-value {top_cat} consignments.",
        "evidence_records": evidence_records,
        "human_approval": "PENDING"
    }


def discount_evidence(
    unified_df: Optional[pd.DataFrame] = None,
    period: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate verifiable evidence trace for promotional discount leakage (discounts >= 35%).
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    filtered = unified_df[unified_df["discount"] >= 35.0].copy()
    filter_desc = ["discount >= 35%"]

    if period:
        filtered = filtered[filtered["year_month"] == period]
        filter_desc.append(f"year_month = '{period}'")

    total_discount_leakage = filtered["discount_amount"].sum()

    cat_summary = (
        filtered.groupby("category")
        .agg(
            discount_loss=("discount_amount", "sum"),
            order_count=("order_id", "count")
        )
        .sort_values("discount_loss", ascending=False)
    )

    top_cat = cat_summary.index[0] if not cat_summary.empty else "N/A"
    top_cat_loss = float(cat_summary.iloc[0]["discount_loss"]) if not cat_summary.empty else 0.0
    cat_share = (top_cat_loss / total_discount_leakage * 100.0) if total_discount_leakage > 0 else 0.0

    evidence_records = filtered[[
        "order_id", "customer_id", "order_date", "category", 
        "unit_price", "quantity", "discount", "discount_amount", "total_amount"
    ]].sort_values(by="discount_amount", ascending=False).reset_index(drop=True)

    filter_str = " AND ".join(filter_desc)

    return {
        "decision_type": "Discount Policy Leakage",
        "sources": ["orders.csv"],
        "filter": filter_str,
        "affected_orders": len(filtered),
        "financial_impact": round(float(total_discount_leakage), 2),
        "primary_category": top_cat,
        "primary_category_impact": round(top_cat_loss, 2),
        "category_share": round(cat_share, 2),
        "calculation": f"Sum of discount deductions where discount >= 35% policy ceiling",
        "conclusion": f"Excessive discount overrides (>=35%) eroded ₹{total_discount_leakage:,.2f} in margin, led by {top_cat}.",
        "recommendation": "Enforce automated authorization limits at checkout for coupon codes exceeding 20% discount.",
        "evidence_records": evidence_records,
        "human_approval": "PENDING"
    }
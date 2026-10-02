import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import get_unified_orders, FAILED_DELIVERY_STATUSES

# ==============================================================================
# LEAKLENS - CUSTOMER & GEOGRAPHIC LEAKAGE ANALYZER
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Customer & Regional Concentration)
# ==============================================================================

def analyze_customer_leakage(
    unified_df: Optional[pd.DataFrame] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Identify customers and customer segments associated with disproportionate refunds and delivery failures.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    df = unified_df.copy()

    # Customer level aggregation
    cust_agg = df.groupby(["customer_id", "customer_segment", "location"]).agg(
        order_count=("order_id", "count"),
        total_spent=("total_amount", "sum"),
        refund_amount=("refund_amount", "sum"),
        refund_count=("refund_amount", lambda x: (x > 0).sum()),
        failed_delivery_val=("total_amount", lambda x: x[df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum()),
        net_revenue=("net_realized_revenue", "sum")
    ).reset_index()

    cust_agg["total_leakage"] = cust_agg["refund_amount"] + cust_agg["failed_delivery_val"]
    cust_agg["refund_rate_pct"] = (cust_agg["refund_amount"] / cust_agg["total_spent"] * 100.0).fillna(0.0).round(1)

    top_refund_custs = cust_agg.sort_values(by="refund_amount", ascending=False).reset_index(drop=True)
    top_cust = top_refund_custs.iloc[0] if not top_refund_custs.empty else None

    # Segment level aggregation
    seg_agg = df.groupby("customer_segment").agg(
        customers=("customer_id", "nunique"),
        orders=("order_id", "count"),
        total_billed=("total_amount", "sum"),
        refund_amount=("refund_amount", "sum"),
        failed_delivery_val=("total_amount", lambda x: x[df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum()),
        net_revenue=("net_realized_revenue", "sum")
    ).reset_index()
    seg_agg["total_leakage"] = seg_agg["refund_amount"] + seg_agg["failed_delivery_val"]
    seg_agg["leakage_share_pct"] = (seg_agg["total_leakage"] / seg_agg["total_leakage"].sum() * 100.0).round(1)
    seg_agg = seg_agg.sort_values(by="total_leakage", ascending=False).reset_index(drop=True)

    top_seg = seg_agg.iloc[0] if not seg_agg.empty else None

    # Evidence records for top refund customer
    if top_cust is not None:
        target_cid = top_cust["customer_id"]
        evidence_df = df[df["customer_id"] == target_cid][[
            "order_id", "customer_id", "order_date", "category",
            "location", "delivery_status", "refund_amount", "refund_reason", "total_amount"
        ]].sort_values(by="refund_amount", ascending=False).reset_index(drop=True)
    else:
        evidence_df = pd.DataFrame()

    return {
        "analysis_type": "Customer & Segment Refund Leakage",
        "top_refund_customers": top_refund_custs.head(limit).to_dict(orient="records"),
        "segment_breakdown": seg_agg.to_dict(orient="records"),
        "primary_customer": {
            "customer_id": top_cust["customer_id"] if top_cust is not None else "N/A",
            "segment": top_cust["customer_segment"] if top_cust is not None else "N/A",
            "location": top_cust["location"] if top_cust is not None else "N/A",
            "refund_amount": round(float(top_cust["refund_amount"]), 2) if top_cust is not None else 0.0,
            "refund_count": int(top_cust["refund_count"]) if top_cust is not None else 0,
            "total_spent": round(float(top_cust["total_spent"]), 2) if top_cust is not None else 0.0
        },
        "primary_segment": {
            "name": top_seg["customer_segment"] if top_seg is not None else "N/A",
            "leakage_amount": round(float(top_seg["total_leakage"]), 2) if top_seg is not None else 0.0,
            "leakage_share": float(top_seg["leakage_share_pct"]) if top_seg is not None else 0.0
        },
        "evidence_trace": {
            "source_datasets": ["customers.csv", "refunds.csv", "orders.csv"],
            "filter_applied": f"customer_id = '{top_cust['customer_id'] if top_cust is not None else 'N/A'}'",
            "calculation_formula": "Customer Refund Amount = Sum of all processed refunds for customer account",
            "sample_record_count": len(evidence_df),
            "evidence_dataframe": evidence_df
        },
        "recommendation": (
            f"Review return policies and order history for top refund account {top_cust['customer_id'] if top_cust is not None else 'N/A'} "
            f"({top_cust['customer_segment'] if top_cust is not None else 'N/A'}, {top_cust['location'] if top_cust is not None else 'N/A'}), "
            f"which logged ₹{top_cust['refund_amount'] if top_cust is not None else 0.0:,.2f} in refunds across {top_cust['refund_count'] if top_cust is not None else 0} claims."
        )
    }


def analyze_location_delivery_risk(
    unified_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Identify metro hubs and logistics routes generating the highest delivery failure rates.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    df = unified_df.copy()

    loc_agg = df.groupby("location").agg(
        total_orders=("order_id", "count"),
        total_billed=("total_amount", "sum"),
        failed_orders=("order_id", lambda x: df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES).sum()),
        failed_revenue=("total_amount", lambda x: x[df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum()),
        net_revenue=("net_realized_revenue", "sum")
    ).reset_index()

    loc_agg["failure_rate_pct"] = (loc_agg["failed_orders"] / loc_agg["total_orders"] * 100.0).round(1)
    loc_agg["loss_share_pct"] = (loc_agg["failed_revenue"] / loc_agg["failed_revenue"].sum() * 100.0).round(1)
    loc_agg = loc_agg.sort_values(by="failed_revenue", ascending=False).reset_index(drop=True)

    worst_loc = loc_agg.iloc[0] if not loc_agg.empty else None

    # Evidence records for worst location
    if worst_loc is not None:
        target_loc = worst_loc["location"]
        evidence_df = df[
            (df["location"] == target_loc) & 
            df["delivery_status"].isin(FAILED_DELIVERY_STATUSES)
        ][[
            "order_id", "customer_id", "order_date", "category",
            "location", "delivery_status", "total_amount"
        ]].sort_values(by="total_amount", ascending=False).reset_index(drop=True)
    else:
        evidence_df = pd.DataFrame()

    return {
        "analysis_type": "Regional Logistics Delivery Risk",
        "location_rankings": loc_agg.to_dict(orient="records"),
        "worst_location": {
            "name": worst_loc["location"] if worst_loc is not None else "N/A",
            "failed_revenue": round(float(worst_loc["failed_revenue"]), 2) if worst_loc is not None else 0.0,
            "failure_rate_pct": float(worst_loc["failure_rate_pct"]) if worst_loc is not None else 0.0,
            "loss_share_pct": float(worst_loc["loss_share_pct"]) if worst_loc is not None else 0.0,
            "failed_orders": int(worst_loc["failed_orders"]) if worst_loc is not None else 0
        },
        "evidence_trace": {
            "source_datasets": ["deliveries.csv", "customers.csv", "orders.csv"],
            "filter_applied": f"location = '{worst_loc['location'] if worst_loc is not None else 'N/A'}' AND delivery_status IN ('Cancelled', 'Failed', 'Returned')",
            "calculation_formula": "Delivery Loss = Sum of order value where delivery status is Cancelled, Failed, or Returned",
            "sample_record_count": len(evidence_df),
            "evidence_dataframe": evidence_df
        },
        "recommendation": (
            f"Prioritize logistics audit in {worst_loc['location'] if worst_loc is not None else 'N/A'}, which accounts for "
            f"₹{worst_loc['failed_revenue'] if worst_loc is not None else 0.0:,.2f} ({worst_loc['loss_share_pct'] if worst_loc is not None else 0.0}% of all delivery losses) "
            f"with an elevated {worst_loc['failure_rate_pct'] if worst_loc is not None else 0.0}% order failure rate."
        )
    }

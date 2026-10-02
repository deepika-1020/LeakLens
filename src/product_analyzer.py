import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import get_unified_orders, FAILED_DELIVERY_STATUSES

# ==============================================================================
# LEAKLENS - PRODUCT LEVEL PERFORMANCE & LEAKAGE ANALYZER
# Role: Data Analytics & AI
# Problem Statement: PS-04 (Granular Product-Level Root Cause)
# ==============================================================================

def analyze_product_leakage(
    unified_df: Optional[pd.DataFrame] = None,
    category: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Deterministically identify products causing the greatest financial drag / revenue leakage
    due to high returns, transit damages, and delivery cancellations.
    """
    if unified_df is None:
        unified_df = get_unified_orders()

    df = unified_df.copy()
    filter_desc = []

    if period:
        df = df[df["year_month"] == period]
        filter_desc.append(f"year_month = '{period}'")

    if category:
        df = df[df["category"] == category]
        filter_desc.append(f"category = '{category}'")

    # Aggregate by Product ID
    prod_agg = df.groupby(["product_id", "category"]).agg(
        order_count=("order_id", "count"),
        units_sold=("quantity", "sum"),
        avg_unit_price=("unit_price", "mean"),
        billed_revenue=("total_amount", "sum"),
        refund_amount=("refund_amount", "sum"),
        refund_orders=("refund_amount", lambda x: (x > 0).sum()),
        failed_delivery_val=("total_amount", lambda x: x[df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES)].sum()),
        failed_orders=("order_id", lambda x: df.loc[x.index, "delivery_status"].isin(FAILED_DELIVERY_STATUSES).sum()),
        net_revenue=("net_realized_revenue", "sum")
    ).reset_index()

    prod_agg["total_leakage"] = prod_agg["refund_amount"] + prod_agg["failed_delivery_val"]
    prod_agg["leakage_ratio_pct"] = (prod_agg["total_leakage"] / prod_agg["billed_revenue"] * 100.0).fillna(0.0).round(1)
    prod_agg["refund_rate_pct"] = (prod_agg["refund_amount"] / prod_agg["billed_revenue"] * 100.0).fillna(0.0).round(1)

    # Sort descending by total financial leakage
    worst_leakage = prod_agg.sort_values(by="total_leakage", ascending=False).reset_index(drop=True)

    # Top selling vs lowest selling
    best_revenue = prod_agg.sort_values(by="net_revenue", ascending=False).reset_index(drop=True)
    lowest_revenue = prod_agg[prod_agg["billed_revenue"] > 0].sort_values(by="billed_revenue", ascending=True).reset_index(drop=True)

    top_loss_prod = worst_leakage.iloc[0] if not worst_leakage.empty else None

    # Extract order-level evidence records for the worst-performing product
    if top_loss_prod is not None:
        target_pid = top_loss_prod["product_id"]
        evidence_df = df[
            (df["product_id"] == target_pid) & 
            ((df["refund_amount"] > 0) | df["delivery_status"].isin(FAILED_DELIVERY_STATUSES))
        ][[
            "order_id", "customer_id", "order_date", "product_id", "category",
            "location", "delivery_status", "refund_amount", "refund_reason", "total_amount"
        ]].sort_values(by=["refund_amount", "total_amount"], ascending=False).reset_index(drop=True)
    else:
        evidence_df = pd.DataFrame()

    total_system_leakage = float(prod_agg["total_leakage"].sum())
    top_prod_leakage = float(top_loss_prod["total_leakage"]) if top_loss_prod is not None else 0.0

    return {
        "analysis_type": "Product Revenue Leakage & Performance",
        "total_products_analyzed": len(prod_agg),
        "worst_leakage_products": worst_leakage.head(limit).to_dict(orient="records"),
        "top_performing_products": best_revenue.head(limit).to_dict(orient="records"),
        "lowest_selling_products": lowest_revenue.head(limit).to_dict(orient="records"),
        "primary_product_at_risk": {
            "product_id": top_loss_prod["product_id"] if top_loss_prod is not None else "N/A",
            "category": top_loss_prod["category"] if top_loss_prod is not None else "N/A",
            "total_leakage": round(top_prod_leakage, 2),
            "refund_amount": round(float(top_loss_prod["refund_amount"]), 2) if top_loss_prod is not None else 0.0,
            "failed_delivery_val": round(float(top_loss_prod["failed_delivery_val"]), 2) if top_loss_prod is not None else 0.0,
            "leakage_ratio_pct": float(top_loss_prod["leakage_ratio_pct"]) if top_loss_prod is not None else 0.0,
            "net_revenue": round(float(top_loss_prod["net_revenue"]), 2) if top_loss_prod is not None else 0.0
        },
        "evidence_trace": {
            "source_datasets": ["orders.csv", "refunds.csv", "deliveries.csv"],
            "filter_applied": f"product_id = '{top_loss_prod['product_id'] if top_loss_prod is not None else 'N/A'}' AND (refund_amount > 0 OR delivery_status IN ('Cancelled', 'Failed', 'Returned'))",
            "calculation_formula": "Total Leakage = Refund Amount + Value of Failed/Cancelled Deliveries",
            "sample_record_count": len(evidence_df),
            "evidence_dataframe": evidence_df
        },
        "recommendation": (
            f"Review catalog placement and logistics for product {top_loss_prod['product_id'] if top_loss_prod is not None else 'N/A'} "
            f"({top_loss_prod['category'] if top_loss_prod is not None else 'N/A'}), which has generated "
            f"₹{top_prod_leakage:,.2f} in combined refunds and delivery failures."
        )
    }

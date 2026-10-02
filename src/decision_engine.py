import pandas as pd
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import load_data, FAILED_DELIVERY_STATUSES

# ==========================================
# LEAKLENS - DECISION ENGINE (BASE MODULE)
# Role: Data Analytics & AI
# ==========================================

def create_refund_decision(orders: pd.DataFrame, refunds: pd.DataFrame, customers: pd.DataFrame):
    data = refunds.merge(
        orders[["order_id", "customer_id", "category", "total_amount"]],
        on="order_id",
        how="left"
    ).merge(
        customers[["customer_id", "customer_segment", "location"]],
        on="customer_id",
        how="left"
    )

    category = (
        data.groupby("category")
        .agg(refund_amount=("refund_amount", "sum"), affected_orders=("order_id", "nunique"))
        .sort_values("refund_amount", ascending=False)
    )

    reason = (
        data.groupby("refund_reason")
        .agg(refund_amount=("refund_amount", "sum"), affected_orders=("order_id", "nunique"))
        .sort_values("refund_amount", ascending=False)
    )

    total_refund = data["refund_amount"].sum()
    top_category = category.index[0]
    category_impact = category.iloc[0]["refund_amount"]
    top_reason = reason.index[0]
    reason_impact = reason.iloc[0]["refund_amount"]
    category_share = (category_impact / total_refund * 100.0) if total_refund > 0 else 0.0

    if category_share >= 40:
        priority = "HIGH"
        rec = f"Investigate refund drivers in the {top_category} category, with priority given to '{top_reason}' cases."
    elif category_share >= 25:
        priority = "MEDIUM"
        rec = f"Review refund patterns in {top_category} category and monitor '{top_reason}' cases."
    else:
        priority = "LOW"
        rec = "Monitor refund patterns and collect additional evidence before taking action."

    return {
        "decision_type": "Refund Leakage",
        "priority": priority,
        "financial_impact": round(float(total_refund), 2),
        "primary_finding": {
            "category": top_category,
            "impact": round(float(category_impact), 2),
            "share_of_refunds": round(float(category_share), 2)
        },
        "secondary_finding": {
            "refund_reason": top_reason,
            "impact": round(float(reason_impact), 2)
        },
        "recommendation": rec,
        "requires_human_approval": True
    }


def create_delivery_decision(orders: pd.DataFrame, deliveries: pd.DataFrame, customers: pd.DataFrame):
    data = deliveries.merge(
        orders[["order_id", "customer_id", "category", "total_amount"]],
        on="order_id",
        how="left"
    ).merge(
        customers[["customer_id", "customer_segment", "location"]],
        on="customer_id",
        how="left"
    )

    failed = data[data["delivery_status"].isin(FAILED_DELIVERY_STATUSES)]

    category = (
        failed.groupby("category")
        .agg(revenue_at_risk=("total_amount", "sum"), affected_orders=("order_id", "nunique"))
        .sort_values("revenue_at_risk", ascending=False)
    )

    total_risk = failed["total_amount"].sum()
    top_category = category.index[0]
    category_risk = category.iloc[0]["revenue_at_risk"]
    category_share = (category_risk / total_risk * 100.0) if total_risk > 0 else 0.0

    if category_share >= 40:
        priority = "HIGH"
        rec = f"Prioritize delivery investigation for {top_category} orders. Review cancellation and failure causes before scaling corrective action."
    elif category_share >= 25:
        priority = "MEDIUM"
        rec = f"Monitor delivery failures in {top_category} and investigate recurring operational causes."
    else:
        priority = "LOW"
        rec = "Continue monitoring delivery failures and collect additional evidence."

    return {
        "decision_type": "Delivery Leakage",
        "priority": priority,
        "financial_impact": round(float(total_risk), 2),
        "primary_finding": {
            "category": top_category,
            "impact": round(float(category_risk), 2),
            "share_of_risk": round(float(category_share), 2)
        },
        "recommendation": rec,
        "requires_human_approval": True
    }


def display_decision(decision):
    print("\n" + "=" * 65)
    print("LEAKLENS DECISION")
    print("=" * 65)
    print(f"Decision Type : {decision['decision_type']}")
    print(f"Priority      : {decision['priority']}")
    print(f"Financial Impact: ₹{decision['financial_impact']:,.2f}")
    print(f"Category      : {decision['primary_finding']['category']}")
    print(f"Impact        : ₹{decision['primary_finding']['impact']:,.2f}")
    print(f"\nRECOMMENDATION\n{decision['recommendation']}")
    print("\nHUMAN APPROVAL REQUIRED: [ APPROVE ]   [ REJECT ]")


def main():
    orders, refunds, customers, deliveries = load_data()
    r_dec = create_refund_decision(orders, refunds, customers)
    d_dec = create_delivery_decision(orders, deliveries, customers)
    display_decision(r_dec)
    display_decision(d_dec)


if __name__ == "__main__":
    main()
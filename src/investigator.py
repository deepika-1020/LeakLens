import pandas as pd
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import load_data, FAILED_DELIVERY_STATUSES

# ==========================================
# LEAKLENS - ROOT CAUSE INVESTIGATOR
# Role: Data Analytics & AI
# ==========================================

def investigate_refunds(orders: pd.DataFrame, refunds: pd.DataFrame, customers: pd.DataFrame):
    refund_orders = refunds.merge(
        orders[["order_id", "customer_id", "category", "total_amount"]],
        on="order_id",
        how="left"
    ).merge(
        customers[["customer_id", "customer_segment", "location"]],
        on="customer_id",
        how="left"
    )

    category_analysis = (
        refund_orders.groupby("category")
        .agg(
            refund_amount=("refund_amount", "sum"),
            refund_orders=("order_id", "nunique")
        )
        .sort_values("refund_amount", ascending=False)
    )

    reason_analysis = (
        refund_orders.groupby("refund_reason")
        .agg(
            refund_amount=("refund_amount", "sum"),
            refund_orders=("order_id", "nunique")
        )
        .sort_values("refund_amount", ascending=False)
    )

    segment_analysis = (
        refund_orders.groupby("customer_segment")
        .agg(
            refund_amount=("refund_amount", "sum"),
            refund_orders=("order_id", "nunique")
        )
        .sort_values("refund_amount", ascending=False)
    )

    total_refund = refund_orders["refund_amount"].sum()

    top_category = category_analysis.index[0]
    top_category_amount = category_analysis.iloc[0]["refund_amount"]

    top_reason = reason_analysis.index[0]
    top_reason_amount = reason_analysis.iloc[0]["refund_amount"]

    top_segment = segment_analysis.index[0]
    top_segment_amount = segment_analysis.iloc[0]["refund_amount"]

    return {
        "investigation_type": "Refund Leakage",
        "financial_impact": round(float(total_refund), 2),
        "primary_root_cause": {
            "dimension": "Product Category",
            "value": top_category,
            "impact": round(float(top_category_amount), 2)
        },
        "secondary_root_cause": {
            "dimension": "Refund Reason",
            "value": top_reason,
            "impact": round(float(top_reason_amount), 2)
        },
        "affected_segment": {
            "segment": top_segment,
            "impact": round(float(top_segment_amount), 2)
        },
        "evidence": {
            "total_refund_orders": int(refund_orders["order_id"].nunique()),
            "top_category_refund_orders": int(category_analysis.iloc[0]["refund_orders"]),
            "top_reason_refund_orders": int(reason_analysis.iloc[0]["refund_orders"])
        }
    }


def investigate_deliveries(orders: pd.DataFrame, deliveries: pd.DataFrame, customers: pd.DataFrame):
    delivery_data = deliveries.merge(
        orders[["order_id", "customer_id", "category", "total_amount"]],
        on="order_id",
        how="left"
    ).merge(
        customers[["customer_id", "customer_segment", "location"]],
        on="customer_id",
        how="left"
    )

    failed = delivery_data[delivery_data["delivery_status"].isin(FAILED_DELIVERY_STATUSES)]

    category_analysis = (
        failed.groupby("category")
        .agg(
            affected_orders=("order_id", "nunique"),
            revenue_at_risk=("total_amount", "sum")
        )
        .sort_values("revenue_at_risk", ascending=False)
    )

    segment_analysis = (
        failed.groupby("customer_segment")
        .agg(
            affected_orders=("order_id", "nunique"),
            revenue_at_risk=("total_amount", "sum")
        )
        .sort_values("revenue_at_risk", ascending=False)
    )

    location_analysis = (
        failed.groupby("location")
        .agg(
            affected_orders=("order_id", "nunique"),
            revenue_at_risk=("total_amount", "sum")
        )
        .sort_values("revenue_at_risk", ascending=False)
    )

    total_revenue_at_risk = failed["total_amount"].sum()

    top_category = category_analysis.index[0]
    top_category_impact = category_analysis.iloc[0]["revenue_at_risk"]

    top_segment = segment_analysis.index[0]
    top_segment_impact = segment_analysis.iloc[0]["revenue_at_risk"]

    top_location = location_analysis.index[0]
    top_location_impact = location_analysis.iloc[0]["revenue_at_risk"]

    return {
        "investigation_type": "Delivery Leakage",
        "financial_impact": round(float(total_revenue_at_risk), 2),
        "primary_root_cause": {
            "dimension": "Product Category",
            "value": top_category,
            "impact": round(float(top_category_impact), 2)
        },
        "affected_segment": {
            "segment": top_segment,
            "impact": round(float(top_segment_impact), 2)
        },
        "affected_location": {
            "location": top_location,
            "impact": round(float(top_location_impact), 2)
        },
        "evidence": {
            "failed_or_cancelled_orders": int(failed["order_id"].nunique())
        }
    }


def print_refund_investigation(result):
    print("\n" + "=" * 60)
    print("REFUND LEAKAGE INVESTIGATION")
    print("=" * 60)
    print(f"\nFinancial Impact: ₹{result['financial_impact']:,.2f}")
    print(f"\nPRIMARY ROOT CAUSE\nCategory: {result['primary_root_cause']['value']}")
    print(f"Impact: ₹{result['primary_root_cause']['impact']:,.2f}")
    print(f"\nSECONDARY ROOT CAUSE\nRefund Reason: {result['secondary_root_cause']['value']}")
    print(f"Impact: ₹{result['secondary_root_cause']['impact']:,.2f}")
    print(f"\nAFFECTED CUSTOMER SEGMENT\nSegment: {result['affected_segment']['segment']}")
    print(f"Impact: ₹{result['affected_segment']['impact']:,.2f}")


def print_delivery_investigation(result):
    print("\n" + "=" * 60)
    print("DELIVERY LEAKAGE INVESTIGATION")
    print("=" * 60)
    print(f"\nFinancial Impact: ₹{result['financial_impact']:,.2f}")
    print(f"\nPRIMARY ROOT CAUSE\nCategory: {result['primary_root_cause']['value']}")
    print(f"Revenue at Risk: ₹{result['primary_root_cause']['impact']:,.2f}")
    print(f"\nAFFECTED LOCATION\nLocation: {result['affected_location']['location']}")
    print(f"Revenue at Risk: ₹{result['affected_location']['impact']:,.2f}")


def main():
    print("\n============================================================")
    print("              LEAKLENS ROOT-CAUSE INVESTIGATOR")
    print("============================================================\n")
    orders, refunds, customers, deliveries = load_data()
    refund_res = investigate_refunds(orders, refunds, customers)
    print_refund_investigation(refund_res)
    delivery_res = investigate_deliveries(orders, deliveries, customers)
    print_delivery_investigation(delivery_res)


if __name__ == "__main__":
    main()
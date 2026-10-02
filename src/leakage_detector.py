import pandas as pd
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_loader import load_data, FAILED_DELIVERY_STATUSES

# ==========================================
# LEAKLENS - LEAKAGE DETECTOR (BASE MODULE)
# Role: Data Analytics & AI
# ==========================================

def detect_refund_leakage(orders: pd.DataFrame, refunds: pd.DataFrame):
    total_revenue = orders["total_amount"].sum()
    total_refunds = refunds["refund_amount"].sum()
    refund_rate = (total_refunds / total_revenue) if total_revenue > 0 else 0.0

    return {
        "leak_type": "Refund Leakage",
        "total_revenue": round(float(total_revenue), 2),
        "total_refunds": round(float(total_refunds), 2),
        "refund_rate": round(float(refund_rate * 100), 2),
        "affected_orders": int(refunds["order_id"].nunique())
    }


def detect_delivery_leakage(orders: pd.DataFrame, deliveries: pd.DataFrame):
    failed = deliveries[deliveries["delivery_status"].isin(FAILED_DELIVERY_STATUSES)]
    affected_orders = failed["order_id"].nunique()

    revenue_at_risk = orders[
        orders["order_id"].isin(failed["order_id"])
    ]["total_amount"].sum()

    return {
        "leak_type": "Delivery Leakage",
        "affected_orders": int(affected_orders),
        "revenue_at_risk": round(float(revenue_at_risk), 2)
    }


def main():
    print("\n========== LEAKLENS ==========")
    print("AI Revenue Leakage Investigator")
    print("================================\n")

    orders, refunds, customers, deliveries = load_data()

    print("Data loaded successfully via data_loader!")
    print(f"Orders      : {len(orders)}")
    print(f"Customers   : {len(customers)}")
    print(f"Refunds     : {len(refunds)}")
    print(f"Deliveries  : {len(deliveries)}")

    print("\n--- REFUND LEAKAGE ---")
    refund_result = detect_refund_leakage(orders, refunds)
    for key, value in refund_result.items():
        print(f"{key}: {value}")

    print("\n--- DELIVERY LEAKAGE ---")
    delivery_result = detect_delivery_leakage(orders, deliveries)
    for key, value in delivery_result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
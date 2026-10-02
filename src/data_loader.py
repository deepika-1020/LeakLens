import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# ==========================================
# LEAKLENS - UNIFIED DATA LOADER & HYGIENE
# Role: Data Analytics & AI
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Standardized delivery failure statuses across all modules
FAILED_DELIVERY_STATUSES = ["Cancelled", "Failed", "Returned"]


def get_data_dir() -> Path:
    """Return the absolute path to the data directory."""
    return DATA_DIR


def load_data(
    data_dir: Optional[Path] = None,
    parse_dates: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load raw CSV datasets with schema validation and datetime parsing.
    Does NOT execute at import time.
    """
    target_dir = Path(data_dir) if data_dir else DATA_DIR

    orders_path = target_dir / "orders.csv"
    refunds_path = target_dir / "refunds.csv"
    customers_path = target_dir / "customers.csv"
    deliveries_path = target_dir / "deliveries.csv"

    for path, name in [
        (orders_path, "orders.csv"),
        (refunds_path, "refunds.csv"),
        (customers_path, "customers.csv"),
        (deliveries_path, "deliveries.csv"),
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required dataset '{name}' not found at {path}. "
                f"Please run generate_data.py first."
            )

    orders = pd.read_csv(orders_path)
    refunds = pd.read_csv(refunds_path)
    customers = pd.read_csv(customers_path)
    deliveries = pd.read_csv(deliveries_path)

    # Schema validation
    _validate_schemas(orders, refunds, customers, deliveries)

    if parse_dates:
        orders["order_date"] = pd.to_datetime(orders["order_date"])
        orders["year_month"] = orders["order_date"].dt.to_period("M").astype(str)
        orders["month_name"] = orders["order_date"].dt.strftime("%B %Y")

        refunds["refund_date"] = pd.to_datetime(refunds["refund_date"])
        refunds["year_month"] = refunds["refund_date"].dt.to_period("M").astype(str)

        deliveries["delivery_date"] = pd.to_datetime(deliveries["delivery_date"])
        deliveries["promised_date"] = pd.to_datetime(deliveries["promised_date"])

        customers["signup_date"] = pd.to_datetime(customers["signup_date"])

    # Ensure numeric types
    orders["total_amount"] = pd.to_numeric(orders["total_amount"], errors="coerce").fillna(0.0)
    orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce").fillna(0.0)
    orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce").fillna(1).astype(int)
    orders["discount"] = pd.to_numeric(orders["discount"], errors="coerce").fillna(0.0)

    refunds["refund_amount"] = pd.to_numeric(refunds["refund_amount"], errors="coerce").fillna(0.0)

    return orders, refunds, customers, deliveries


def _validate_schemas(
    orders: pd.DataFrame,
    refunds: pd.DataFrame,
    customers: pd.DataFrame,
    deliveries: pd.DataFrame
) -> None:
    """Validate that all mandatory business columns exist."""
    required_cols = {
        "orders": {"order_id", "customer_id", "order_date", "category", "quantity", "unit_price", "discount", "total_amount", "status"},
        "refunds": {"refund_id", "order_id", "refund_date", "refund_amount", "refund_reason"},
        "customers": {"customer_id", "customer_segment", "location", "signup_date"},
        "deliveries": {"order_id", "delivery_date", "promised_date", "delivery_status"}
    }

    missing_orders = required_cols["orders"] - set(orders.columns)
    if missing_orders:
        raise ValueError(f"orders.csv missing required columns: {missing_orders}")

    missing_refunds = required_cols["refunds"] - set(refunds.columns)
    if missing_refunds:
        raise ValueError(f"refunds.csv missing required columns: {missing_refunds}")

    missing_customers = required_cols["customers"] - set(customers.columns)
    if missing_customers:
        raise ValueError(f"customers.csv missing required columns: {missing_customers}")

    missing_deliveries = required_cols["deliveries"] - set(deliveries.columns)
    if missing_deliveries:
        raise ValueError(f"deliveries.csv missing required columns: {missing_deliveries}")


def get_unified_orders(
    orders: Optional[pd.DataFrame] = None,
    refunds: Optional[pd.DataFrame] = None,
    customers: Optional[pd.DataFrame] = None,
    deliveries: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Produce a centralized, joined analytical DataFrame at the order level.
    Avoids duplicate joins across multiple analytical modules.
    """
    if orders is None or refunds is None or customers is None or deliveries is None:
        orders, refunds, customers, deliveries = load_data()

    # Join customer dimensions
    unified = orders.merge(
        customers[["customer_id", "customer_segment", "location"]],
        on="customer_id",
        how="left"
    )

    # Join delivery status
    # In case of duplicate deliveries per order, take latest/most severe
    deliv_dedup = deliveries.sort_values("delivery_date").groupby("order_id").last().reset_index()
    unified = unified.merge(
        deliv_dedup[["order_id", "delivery_status", "delivery_date", "promised_date"]],
        on="order_id",
        how="left"
    )

    # Join refund aggregated values (an order could theoretically have multiple refund line items)
    refund_agg = refunds.groupby("order_id").agg(
        refund_amount=("refund_amount", "sum"),
        refund_reason=("refund_reason", lambda x: " | ".join(sorted(set(x)))),
        refund_date=("refund_date", "max"),
        refund_count=("refund_id", "count")
    ).reset_index()

    unified = unified.merge(
        refund_agg,
        on="order_id",
        how="left"
    )

    # Fill default refund columns for orders with no refund
    unified["refund_amount"] = unified["refund_amount"].fillna(0.0)
    unified["refund_reason"] = unified["refund_reason"].fillna("None")
    unified["refund_count"] = unified["refund_count"].fillna(0).astype(int)

    # Derived analytical columns
    unified["gross_revenue"] = unified["quantity"] * unified["unit_price"]
    unified["discount_amount"] = unified["gross_revenue"] * (unified["discount"] / 100.0)
    
    # Financial classification flags
    unified["is_failed_delivery"] = unified["delivery_status"].isin(FAILED_DELIVERY_STATUSES)
    unified["is_cancelled_order"] = unified["status"] == "Cancelled"
    unified["is_refunded"] = unified["refund_amount"] > 0
    unified["is_discount_leakage"] = unified["discount"] >= 35.0  # Controlled discount threshold

    # Net Realized Revenue calculation for an order:
    # If delivery failed or order cancelled, realized revenue is 0.
    # Otherwise, it is total_amount (billed after discount) minus refund_amount.
    def compute_net(row):
        if row["is_failed_delivery"] or row["is_cancelled_order"]:
            return 0.0
        return max(0.0, row["total_amount"] - row["refund_amount"])

    unified["net_realized_revenue"] = unified.apply(compute_net, axis=1)

    return unified


if __name__ == "__main__":
    orders, refunds, customers, deliveries = load_data()
    print("DataLoader test successful!")
    print(f"Orders: {len(orders)}, Refunds: {len(refunds)}, Customers: {len(customers)}, Deliveries: {len(deliveries)}")
    unified = get_unified_orders(orders, refunds, customers, deliveries)
    print(f"Unified analytical dataset: {len(unified)} rows, {len(unified.columns)} columns.")
    print("Net Realized Revenue Total: ₹", round(unified["net_realized_revenue"].sum(), 2))

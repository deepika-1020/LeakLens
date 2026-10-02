import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# LEAKLENS - REPRODUCIBLE SYNTHETIC BUSINESS DATASET GENERATOR
# Role: Data Analytics & AI
# Problem Statement: PS-04 (AI Decision Engine for Business Data)
#
# CONTROLLED BUSINESS EVENT DOCUMENTATION (Seed = 42):
# To enable realistic Month-over-Month (MoM) revenue decline investigation
# for queries such as "Why did revenue decline last month?" (August vs September 2026):
# 1. Base Period (Jan - Aug 2026): Steady operational baseline.
# 2. September 2026 Disruption Event:
#    - Major 3PL logistics disruption in South Hub (Hyderabad & Bangalore) causing
#      Electronics delivery failure/cancellation rates to surge (~45%).
#    - Increased Electronics customer refund requests (~60% rate) citing
#      "Damaged" (transit handling) and "Late Delivery".
#    - Promotional discount leakage: occasional unauthorized 35%-50% discount codes.
# This produces a genuine, statistically measurable Net Revenue decline in
# September 2026 vs August 2026 with fully traceable root causes.
# ==============================================================================

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Dataset configuration
NUM_CUSTOMERS = 300
NUM_ORDERS = 2000
START_DATE = datetime(2026, 1, 1)

# ==============================================================================
# 1. CUSTOMERS
# ==============================================================================

customers = []
segments = ["Standard", "Premium", "Enterprise"]
locations = ["Chennai", "Bangalore", "Hyderabad", "Mumbai", "Delhi"]

for i in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "customer_id": f"CUST{i:04d}",
        "customer_segment": random.choice(segments),
        "location": random.choice(locations),
        "signup_date": (
            START_DATE - timedelta(days=random.randint(30, 1000))
        ).strftime("%Y-%m-%d")
    })

customers_df = pd.DataFrame(customers)
customer_ids = customers_df["customer_id"].tolist()
# Quick lookup mapping for customer location
cust_location_map = dict(zip(customers_df["customer_id"], customers_df["location"]))

# ==============================================================================
# 2. ORDERS
# ==============================================================================

orders = []
products = {
    "Electronics": (10000, 50000),
    "Home": (1000, 15000),
    "Fashion": (500, 8000),
    "Beauty": (300, 5000)
}

for i in range(1, NUM_ORDERS + 1):
    category = random.choice(list(products.keys()))
    min_price, max_price = products[category]
    quantity = random.randint(1, 3)
    unit_price = random.randint(min_price, max_price)

    # Standard discount distribution
    discount = random.choice([0, 5, 10, 15, 20])

    # Controlled discount leakage: periodic discount overrides
    if i % 173 == 0 or (i % 89 == 0 and category in ["Fashion", "Home"]):
        discount = random.randint(35, 50)

    # Uniform timeline across 270 days (Jan 1, 2026 to Sep 28, 2026)
    order_date = START_DATE + timedelta(days=random.randint(0, 270))
    is_september = order_date.month == 9

    total_amount = quantity * unit_price * (1 - discount / 100.0)

    # Status: most are Completed, small natural cancellation baseline
    order_status = "Completed"
    if random.random() < 0.08:
        order_status = "Cancelled"

    orders.append({
        "order_id": f"ORD{i:05d}",
        "customer_id": random.choice(customer_ids),
        "order_date": order_date.strftime("%Y-%m-%d"),
        "product_id": f"P{random.randint(1, 100):03d}",
        "category": category,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
        "total_amount": round(total_amount, 2),
        "status": order_status
    })

orders_df = pd.DataFrame(orders)

# ==============================================================================
# 3. REFUNDS
# ==============================================================================

refunds = []
refund_id = 1

for _, order in orders_df.iterrows():
    order_number = int(order["order_id"][3:])
    order_dt = datetime.strptime(order["order_date"], "%Y-%m-%d")
    is_september = order_dt.month == 9
    cat = order["category"]

    # Baseline refund probability
    refund_probability = 0.06

    # Controlled injection 1: all-year periodic refund cluster
    if order_number % 97 == 0:
        refund_probability = 0.85

    # Controlled injection 2: September 2026 Electronics quality/handling surge
    if is_september and cat == "Electronics":
        refund_probability = 0.48

    if random.random() < refund_probability and order["status"] != "Cancelled":
        refund_amount = round(
            order["total_amount"] * random.uniform(0.6, 1.0),
            2
        )

        refund_date = order_dt + timedelta(days=random.randint(1, 14))

        if is_september and cat == "Electronics":
            reason = random.choice(["Damaged", "Late Delivery", "Wrong Product"])
        else:
            reason = random.choice([
                "Damaged",
                "Customer Request",
                "Wrong Product",
                "Late Delivery"
            ])

        refunds.append({
            "refund_id": f"REF{refund_id:05d}",
            "order_id": order["order_id"],
            "refund_date": refund_date.strftime("%Y-%m-%d"),
            "refund_amount": refund_amount,
            "refund_reason": reason
        })
        refund_id += 1

refunds_df = pd.DataFrame(refunds)

# ==============================================================================
# 4. DELIVERIES
# ==============================================================================

deliveries = []

for _, order in orders_df.iterrows():
    order_number = int(order["order_id"][3:])
    order_dt = datetime.strptime(order["order_date"], "%Y-%m-%d")
    is_september = order_dt.month == 9
    cat = order["category"]
    cust_loc = cust_location_map.get(order["customer_id"], "Unknown")

    promised_date = order_dt + timedelta(days=random.randint(2, 6))

    # Default delivery outcome distribution
    # Delivered: 82%, Late: 10%, Cancelled: 5%, Failed: 3%
    delivery_status = random.choices(
        ["Delivered", "Late", "Cancelled", "Failed"],
        weights=[82, 10, 5, 3]
    )[0]

    # Controlled injection 1: all-year periodic failure
    if order_number % 113 == 0:
        delivery_status = random.choice(["Cancelled", "Failed", "Returned"])

    # Controlled injection 2: September 2026 Electronics logistics disruption
    # concentrated in Hyderabad and Bangalore
    if is_september and cat == "Electronics":
        if cust_loc in ["Hyderabad", "Bangalore"]:
            delivery_status = random.choices(
                ["Failed", "Cancelled", "Returned", "Late", "Delivered"],
                weights=[25, 20, 15, 20, 20]
            )[0]
        else:
            delivery_status = random.choices(
                ["Failed", "Cancelled", "Returned", "Delivered"],
                weights=[15, 15, 10, 60]
            )[0]

    # If the order was cancelled upfront, delivery is Cancelled
    if order["status"] == "Cancelled":
        delivery_status = "Cancelled"

    delivery_date = promised_date + timedelta(days=random.randint(-1, 5))

    deliveries.append({
        "order_id": order["order_id"],
        "delivery_date": delivery_date.strftime("%Y-%m-%d"),
        "promised_date": promised_date.strftime("%Y-%m-%d"),
        "delivery_status": delivery_status
    })

deliveries_df = pd.DataFrame(deliveries)

# ==============================================================================
# 5. PERSIST DATASETS
# ==============================================================================

customers_df.to_csv(DATA_DIR / "customers.csv", index=False)
orders_df.to_csv(DATA_DIR / "orders.csv", index=False)
refunds_df.to_csv(DATA_DIR / "refunds.csv", index=False)
deliveries_df.to_csv(DATA_DIR / "deliveries.csv", index=False)

print("\n=======================================================")
print("            LEAKLENS DATASET GENERATED")
print("=======================================================")
print(f"Customers  : {len(customers_df)}")
print(f"Orders     : {len(orders_df)}")
print(f"Refunds    : {len(refunds_df)}")
print(f"Deliveries : {len(deliveries_df)}")
print(f"Path       : {DATA_DIR}")
print("Random Seed: 42 (100% Reproducible)")
print("Business Event: September 2026 Electronics Logistics & Refund Disruption")
print("=======================================================\n")
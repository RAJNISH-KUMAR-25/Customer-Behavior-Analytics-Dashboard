"""
generate_data.py
Generates synthetic customer transaction dataset (100,000+ records)
for Customer Behavior Analytics Dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

NUM_CUSTOMERS = 5000
NUM_TRANSACTIONS = 100000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)

PRODUCT_CATEGORIES = [
    "Electronics", "Clothing", "Home & Garden", "Sports",
    "Books", "Beauty", "Toys", "Food & Grocery", "Automotive", "Health"
]
REGIONS = ["North", "South", "East", "West", "Central"]
CHANNELS = ["Online", "In-Store", "Mobile App", "Phone"]
SEGMENTS = ["Premium", "Regular", "Occasional", "New"]


def generate_customers(n=NUM_CUSTOMERS):
    print(f"Generating {n} customers...")
    customer_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, n + 1)]
    ages = np.random.randint(18, 75, n)
    genders = np.random.choice(["Male", "Female", "Other"], n, p=[0.48, 0.48, 0.04])
    regions = np.random.choice(REGIONS, n)
    segments = np.random.choice(SEGMENTS, n, p=[0.15, 0.45, 0.25, 0.15])
    join_dates = [START_DATE + timedelta(days=random.randint(0, 365)) for _ in range(n)]
    emails = [f"customer{i}@email.com" for i in range(1, n + 1)]
    loyalty_points = np.random.randint(0, 10000, n)
    is_churned = np.where(
        np.array(segments) == "Occasional",
        np.random.choice([0, 1], n, p=[0.5, 0.5]),
        np.random.choice([0, 1], n, p=[0.85, 0.15])
    )
    return pd.DataFrame({
        "customer_id": customer_ids, "age": ages, "gender": genders,
        "region": regions, "segment": segments, "email": emails,
        "join_date": join_dates, "loyalty_points": loyalty_points,
        "is_churned": is_churned
    })


def generate_transactions(customers_df, n=NUM_TRANSACTIONS):
    print(f"Generating {n} transactions...")
    customer_ids = customers_df["customer_id"].tolist()
    weights = customers_df["segment"].map(
        {"Premium": 0.4, "Regular": 0.35, "Occasional": 0.15, "New": 0.1}
    ).values
    weights = weights / weights.sum()
    selected_customers = np.random.choice(customer_ids, n, p=weights)
    transaction_ids = [f"TXN{str(i).zfill(7)}" for i in range(1, n + 1)]
    dates = [START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days)) for _ in range(n)]
    categories = np.random.choice(PRODUCT_CATEGORIES, n)
    channels = np.random.choice(CHANNELS, n, p=[0.45, 0.30, 0.20, 0.05])
    base_amounts = {
        "Electronics": (50, 2000), "Clothing": (20, 300), "Home & Garden": (30, 500),
        "Sports": (25, 600), "Books": (10, 100), "Beauty": (15, 200),
        "Toys": (10, 150), "Food & Grocery": (20, 250), "Automotive": (50, 1000), "Health": (15, 300)
    }
    amounts = np.array([round(random.uniform(*base_amounts[cat]), 2) for cat in categories])
    discounts = np.round(np.random.choice([0, 5, 10, 15, 20, 25], n, p=[0.4, 0.15, 0.2, 0.1, 0.1, 0.05]), 2)
    final_amounts = np.round(amounts * (1 - discounts / 100), 2)
    quantities = np.random.randint(1, 6, n)
    ratings = np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.08, 0.17, 0.40, 0.30])
    returns = np.random.choice([0, 1], n, p=[0.92, 0.08])
    payment_methods = np.random.choice(
        ["Credit Card", "Debit Card", "UPI", "Cash", "Wallet"], n, p=[0.35, 0.25, 0.20, 0.10, 0.10]
    )
    df = pd.DataFrame({
        "transaction_id": transaction_ids, "customer_id": selected_customers,
        "transaction_date": dates, "product_category": categories,
        "channel": channels, "amount": amounts, "discount_percent": discounts,
        "final_amount": final_amounts, "quantity": quantities, "rating": ratings,
        "is_returned": returns, "payment_method": payment_methods
    })
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df.sort_values("transaction_date").reset_index(drop=True)


def main():
    os.makedirs("../../data/raw", exist_ok=True)
    customers_df = generate_customers()
    transactions_df = generate_transactions(customers_df)
    customers_df.to_csv("../../data/raw/customers.csv", index=False)
    transactions_df.to_csv("../../data/raw/transactions.csv", index=False)
    print(f"\n✅ Data Generation Complete!")
    print(f"   Customers   : {len(customers_df):,} records")
    print(f"   Transactions: {len(transactions_df):,} records")
    return customers_df, transactions_df


if __name__ == "__main__":
    main()

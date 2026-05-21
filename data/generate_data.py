import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

NUM_CUSTOMERS = 1000
NUM_TRANSACTIONS = 100000

# Generate customers
customer_ids = [f"CUST{str(i).zfill(5)}" for i in range(1, NUM_CUSTOMERS + 1)]
regions = ["North", "South", "East", "West"]
segments = ["Premium", "Regular", "Budget"]

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "age": np.random.randint(18, 70, NUM_CUSTOMERS),
    "region": np.random.choice(regions, NUM_CUSTOMERS),
    "segment": np.random.choice(segments, NUM_CUSTOMERS, p=[0.2, 0.5, 0.3]),
    "join_date": [
        (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
        for _ in range(NUM_CUSTOMERS)
    ]
})

# Generate transactions
categories = ["Electronics", "Clothing", "Grocery", "Home", "Sports"]
start_date = datetime(2022, 1, 1)

transactions = pd.DataFrame({
    "transaction_id": [f"TXN{str(i).zfill(7)}" for i in range(1, NUM_TRANSACTIONS + 1)],
    "customer_id": np.random.choice(customer_ids, NUM_TRANSACTIONS),
    "date": [
        (start_date + timedelta(days=random.randint(0, 730))).strftime("%Y-%m-%d")
        for _ in range(NUM_TRANSACTIONS)
    ],
    "category": np.random.choice(categories, NUM_TRANSACTIONS),
    "amount": np.round(np.random.exponential(scale=150, size=NUM_TRANSACTIONS) + 10, 2),
    "quantity": np.random.randint(1, 10, NUM_TRANSACTIONS),
    "returned": np.random.choice([0, 1], NUM_TRANSACTIONS, p=[0.92, 0.08])
})

customers.to_csv("customers.csv", index=False)
transactions.to_csv("transactions.csv", index=False)
print(f"Generated {len(customers)} customers and {len(transactions)} transactions.")

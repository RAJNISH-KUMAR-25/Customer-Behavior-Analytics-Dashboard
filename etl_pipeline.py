import pandas as pd
import numpy as np

def load_data():
    customers = pd.read_csv("data/customers.csv")
    transactions = pd.read_csv("data/transactions.csv")
    return customers, transactions

def clean_data(customers, transactions):
    # Drop duplicates
    customers.drop_duplicates(subset="customer_id", inplace=True)
    transactions.drop_duplicates(subset="transaction_id", inplace=True)

    # Fill missing values
    transactions["amount"].fillna(transactions["amount"].median(), inplace=True)
    transactions["quantity"].fillna(1, inplace=True)

    # Remove negative amounts
    transactions = transactions[transactions["amount"] > 0]

    # Parse dates
    transactions["date"] = pd.to_datetime(transactions["date"])
    customers["join_date"] = pd.to_datetime(customers["join_date"])

    return customers, transactions

def transform_data(customers, transactions):
    # Merge
    df = transactions.merge(customers, on="customer_id", how="left")

    # Feature engineering
    df["revenue"] = df["amount"] * df["quantity"]
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year"] = df["date"].dt.year

    # RFM metrics per customer
    snapshot_date = df["date"].max()
    rfm = df.groupby("customer_id").agg(
        recency=("date", lambda x: (snapshot_date - x.max()).days),
        frequency=("transaction_id", "count"),
        monetary=("revenue", "sum")
    ).reset_index()

    return df, rfm

def validate_data(df):
    print("=== Data Validation ===")
    print(f"Total records     : {len(df)}")
    print(f"Missing values    :\n{df.isnull().sum()[df.isnull().sum() > 0]}")
    print(f"Negative amounts  : {(df['amount'] < 0).sum()}")
    print(f"Date range        : {df['date'].min()} → {df['date'].max()}")
    print("Validation passed!")

if __name__ == "__main__":
    customers, transactions = load_data()
    customers, transactions = clean_data(customers, transactions)
    df, rfm = transform_data(customers, transactions)
    validate_data(df)

    df.to_csv("data/processed_transactions.csv", index=False)
    rfm.to_csv("data/rfm_scores.csv", index=False)
    print("ETL complete. Files saved to data/")

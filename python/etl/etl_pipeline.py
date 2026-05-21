"""
etl_pipeline.py
ETL Workflow: Extract → Transform → Load
Handles data cleaning, preprocessing, validation, and feature engineering
for Customer Behavior Analytics Dashboard
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("../../reports/etl_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"


# ─────────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────────

def extract_data():
    """Load raw CSVs from data/raw/"""
    logger.info("EXTRACT: Loading raw data...")
    customers = pd.read_csv(f"{RAW_DIR}/customers.csv", parse_dates=["join_date"])
    transactions = pd.read_csv(f"{RAW_DIR}/transactions.csv", parse_dates=["transaction_date"])
    logger.info(f"  Customers   : {len(customers):,} rows")
    logger.info(f"  Transactions: {len(transactions):,} rows")
    return customers, transactions


# ─────────────────────────────────────────────
# TRANSFORM – CUSTOMERS
# ─────────────────────────────────────────────

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("TRANSFORM: Cleaning customer data...")
    original_len = len(df)

    # Drop exact duplicates
    df = df.drop_duplicates(subset=["customer_id"])

    # Handle missing values
    df["age"] = df["age"].fillna(df["age"].median())
    df["gender"] = df["gender"].fillna("Unknown")
    df["loyalty_points"] = df["loyalty_points"].fillna(0)

    # Validate age range
    df = df[(df["age"] >= 18) & (df["age"] <= 100)]

    # Feature: Age group
    df["age_group"] = pd.cut(
        df["age"], bins=[17, 25, 35, 45, 55, 65, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
    )

    # Standardize text fields
    df["gender"] = df["gender"].str.strip().str.title()
    df["segment"] = df["segment"].str.strip().str.title()
    df["region"] = df["region"].str.strip().str.title()

    # Customer tenure in days
    df["tenure_days"] = (datetime(2024, 12, 31) - df["join_date"]).dt.days

    logger.info(f"  Cleaned: {original_len:,} → {len(df):,} rows ({original_len - len(df)} removed)")
    return df


# ─────────────────────────────────────────────
# TRANSFORM – TRANSACTIONS
# ─────────────────────────────────────────────

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("TRANSFORM: Cleaning transaction data...")
    original_len = len(df)

    # Drop duplicates
    df = df.drop_duplicates(subset=["transaction_id"])

    # Remove invalid amounts
    df = df[df["final_amount"] > 0]
    df = df[df["quantity"] > 0]

    # Validate discount range
    df["discount_percent"] = df["discount_percent"].clip(0, 100)

    # Date features
    df["year"] = df["transaction_date"].dt.year
    df["month"] = df["transaction_date"].dt.month
    df["month_name"] = df["transaction_date"].dt.strftime("%b")
    df["quarter"] = df["transaction_date"].dt.quarter
    df["day_of_week"] = df["transaction_date"].dt.day_name()
    df["is_weekend"] = df["transaction_date"].dt.dayofweek >= 5
    df["week_of_year"] = df["transaction_date"].dt.isocalendar().week.astype(int)

    # Revenue metric
    df["revenue"] = df["final_amount"] * df["quantity"]

    # Discount bucket
    df["discount_bucket"] = pd.cut(
        df["discount_percent"], bins=[-1, 0, 10, 20, 100],
        labels=["No Discount", "Low (1-10%)", "Mid (11-20%)", "High (21%+)"]
    )

    logger.info(f"  Cleaned: {original_len:,} → {len(df):,} rows ({original_len - len(df)} removed)")
    return df


# ─────────────────────────────────────────────
# FEATURE ENGINEERING – RFM
# ─────────────────────────────────────────────

def compute_rfm(transactions_df: pd.DataFrame) -> pd.DataFrame:
    logger.info("FEATURE ENG: Computing RFM metrics...")
    snapshot_date = pd.Timestamp("2025-01-01")
    rfm = transactions_df[transactions_df["is_returned"] == 0].groupby("customer_id").agg(
        recency=("transaction_date", lambda x: (snapshot_date - x.max()).days),
        frequency=("transaction_id", "count"),
        monetary=("revenue", "sum")
    ).reset_index()

    # Score each dimension (1=worst, 5=best)
    rfm["R"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["rfm_score"] = rfm["R"] + rfm["F"] + rfm["M"]

    def rfm_segment(score):
        if score >= 13:
            return "Champions"
        elif score >= 10:
            return "Loyal Customers"
        elif score >= 7:
            return "Potential Loyalists"
        elif score >= 5:
            return "At Risk"
        else:
            return "Lost"

    rfm["rfm_segment"] = rfm["rfm_score"].apply(rfm_segment)
    logger.info(f"  RFM segments:\n{rfm['rfm_segment'].value_counts().to_string()}")
    return rfm


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

def validate_data(customers_df, transactions_df, rfm_df):
    logger.info("VALIDATE: Running data quality checks...")
    issues = []

    # Null checks
    cust_nulls = customers_df[["customer_id", "age", "segment", "region"]].isnull().sum()
    if cust_nulls.any():
        issues.append(f"Customer nulls: {cust_nulls[cust_nulls > 0].to_dict()}")

    txn_nulls = transactions_df[["transaction_id", "customer_id", "final_amount"]].isnull().sum()
    if txn_nulls.any():
        issues.append(f"Transaction nulls: {txn_nulls[txn_nulls > 0].to_dict()}")

    # Orphan transactions (no matching customer)
    valid_customers = set(customers_df["customer_id"])
    orphans = transactions_df[~transactions_df["customer_id"].isin(valid_customers)]
    if len(orphans) > 0:
        issues.append(f"Orphan transactions: {len(orphans)}")

    # Amount sanity
    neg_amounts = (transactions_df["final_amount"] < 0).sum()
    if neg_amounts > 0:
        issues.append(f"Negative amounts: {neg_amounts}")

    if issues:
        for issue in issues:
            logger.warning(f"  ⚠️  {issue}")
    else:
        logger.info("  ✅ All data quality checks passed!")

    return len(issues) == 0


# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────

def load_data(customers_df, transactions_df, rfm_df):
    logger.info("LOAD: Saving processed data...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    customers_df.to_csv(f"{PROCESSED_DIR}/customers_cleaned.csv", index=False)
    transactions_df.to_csv(f"{PROCESSED_DIR}/transactions_cleaned.csv", index=False)
    rfm_df.to_csv(f"{PROCESSED_DIR}/rfm_scores.csv", index=False)

    # Monthly summary for Power BI
    monthly = transactions_df.groupby(["year", "month", "month_name", "product_category"]).agg(
        total_revenue=("revenue", "sum"),
        total_transactions=("transaction_id", "count"),
        avg_order_value=("final_amount", "mean"),
        return_rate=("is_returned", "mean")
    ).reset_index()
    monthly.to_csv(f"{PROCESSED_DIR}/monthly_summary.csv", index=False)

    # Customer 360 (merged)
    customer_360 = customers_df.merge(rfm_df, on="customer_id", how="left")
    customer_360.to_csv(f"{PROCESSED_DIR}/customer_360.csv", index=False)

    logger.info(f"  ✅ All processed files saved to {PROCESSED_DIR}/")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run_etl():
    logger.info("=" * 60)
    logger.info("  CUSTOMER BEHAVIOR ANALYTICS – ETL PIPELINE")
    logger.info("=" * 60)

    customers, transactions = extract_data()
    customers = clean_customers(customers)
    transactions = clean_transactions(transactions)
    rfm = compute_rfm(transactions)
    validate_data(customers, transactions, rfm)
    load_data(customers, transactions, rfm)

    logger.info("=" * 60)
    logger.info("  ETL PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    return customers, transactions, rfm


if __name__ == "__main__":
    run_etl()

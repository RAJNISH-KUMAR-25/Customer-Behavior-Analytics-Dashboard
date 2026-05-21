"""
test_pipeline.py
Basic unit tests for ETL and model pipeline components
Run with: python -m pytest tests/ -v
"""

import sys
import os
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from python.etl.generate_data import generate_customers, generate_transactions
from python.etl.etl_pipeline import clean_customers, clean_transactions, compute_rfm


# ─────────────────────────────────────────────
# TESTS: DATA GENERATION
# ─────────────────────────────────────────────

class TestDataGeneration:

    def test_customers_shape(self):
        df = generate_customers(n=100)
        assert len(df) == 100
        assert "customer_id" in df.columns

    def test_customer_ids_unique(self):
        df = generate_customers(n=200)
        assert df["customer_id"].nunique() == 200

    def test_age_range(self):
        df = generate_customers(n=500)
        assert df["age"].min() >= 18
        assert df["age"].max() <= 75

    def test_segments(self):
        df = generate_customers(n=500)
        valid_segments = {"Premium", "Regular", "Occasional", "New"}
        assert set(df["segment"].unique()).issubset(valid_segments)

    def test_transactions_shape(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=500)
        assert len(txns) == 500

    def test_transaction_ids_unique(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=300)
        assert txns["transaction_id"].nunique() == 300

    def test_amounts_positive(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=200)
        assert (txns["final_amount"] > 0).all()

    def test_discount_range(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=200)
        assert txns["discount_percent"].min() >= 0
        assert txns["discount_percent"].max() <= 100


# ─────────────────────────────────────────────
# TESTS: ETL CLEANING
# ─────────────────────────────────────────────

class TestETLCleaning:

    def setup_method(self):
        self.customers = generate_customers(n=100)
        self.transactions = generate_transactions(self.customers, n=1000)

    def test_clean_customers_no_nulls_in_key_cols(self):
        cleaned = clean_customers(self.customers.copy())
        assert cleaned["customer_id"].isnull().sum() == 0

    def test_clean_customers_age_group_added(self):
        cleaned = clean_customers(self.customers.copy())
        assert "age_group" in cleaned.columns

    def test_clean_customers_tenure_days_positive(self):
        cleaned = clean_customers(self.customers.copy())
        assert (cleaned["tenure_days"] >= 0).all()

    def test_clean_transactions_date_features(self):
        cleaned = clean_transactions(self.transactions.copy())
        assert "year" in cleaned.columns
        assert "month" in cleaned.columns
        assert "quarter" in cleaned.columns

    def test_clean_transactions_revenue_column(self):
        cleaned = clean_transactions(self.transactions.copy())
        assert "revenue" in cleaned.columns
        assert (cleaned["revenue"] > 0).all()

    def test_rfm_computation(self):
        cleaned_txns = clean_transactions(self.transactions.copy())
        rfm = compute_rfm(cleaned_txns)
        assert "recency" in rfm.columns
        assert "frequency" in rfm.columns
        assert "monetary" in rfm.columns
        assert "rfm_segment" in rfm.columns

    def test_rfm_segments_valid(self):
        cleaned_txns = clean_transactions(self.transactions.copy())
        rfm = compute_rfm(cleaned_txns)
        valid_segs = {"Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost"}
        assert set(rfm["rfm_segment"].unique()).issubset(valid_segs)

    def test_rfm_monetary_positive(self):
        cleaned_txns = clean_transactions(self.transactions.copy())
        rfm = compute_rfm(cleaned_txns)
        assert (rfm["monetary"] > 0).all()


# ─────────────────────────────────────────────
# TESTS: DATA INTEGRITY
# ─────────────────────────────────────────────

class TestDataIntegrity:

    def test_no_duplicate_customer_ids(self):
        df = generate_customers(n=200)
        assert df["customer_id"].duplicated().sum() == 0

    def test_no_duplicate_transaction_ids(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=500)
        assert txns["transaction_id"].duplicated().sum() == 0

    def test_is_churned_binary(self):
        df = generate_customers(n=200)
        assert set(df["is_churned"].unique()).issubset({0, 1})

    def test_rating_range(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=300)
        assert txns["rating"].min() >= 1
        assert txns["rating"].max() <= 5

    def test_is_returned_binary(self):
        customers = generate_customers(n=50)
        txns = generate_transactions(customers, n=300)
        assert set(txns["is_returned"].unique()).issubset({0, 1})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

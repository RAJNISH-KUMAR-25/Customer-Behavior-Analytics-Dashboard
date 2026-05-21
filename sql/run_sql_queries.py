"""
run_sql_queries.py
Loads cleaned data into SQLite, executes all analytical SQL queries,
and exports results to CSV for Power BI and Excel integration.
"""

import sqlite3
import pandas as pd
import os

PROCESSED_DIR = "../../data/processed"
EXPORTS_DIR = "../../data/exports"
DB_PATH = "../../data/customer_analytics.db"

os.makedirs(EXPORTS_DIR, exist_ok=True)

QUERIES = {
    "kpi_summary": """
        SELECT
            COUNT(DISTINCT c.customer_id)                        AS total_customers,
            COUNT(DISTINCT t.transaction_id)                     AS total_transactions,
            ROUND(SUM(t.final_amount * t.quantity), 2)           AS total_revenue,
            ROUND(AVG(t.final_amount), 2)                        AS avg_order_value,
            ROUND(AVG(t.rating), 2)                              AS avg_customer_rating,
            ROUND(AVG(t.is_returned) * 100, 2)                   AS return_rate_pct,
            ROUND(AVG(c.is_churned) * 100, 2)                    AS churn_rate_pct
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
    """,

    "monthly_revenue": """
        SELECT
            STRFTIME('%Y', transaction_date) AS year,
            STRFTIME('%m', transaction_date) AS month,
            COUNT(transaction_id) AS transaction_count,
            ROUND(SUM(final_amount * quantity), 2) AS revenue,
            ROUND(AVG(final_amount), 2) AS avg_order_value
        FROM transactions
        GROUP BY year, month
        ORDER BY year, month
    """,

    "category_performance": """
        SELECT
            product_category,
            COUNT(transaction_id) AS total_orders,
            ROUND(SUM(final_amount * quantity), 2) AS total_revenue,
            ROUND(AVG(final_amount), 2) AS avg_order_value,
            ROUND(AVG(rating), 2) AS avg_rating,
            ROUND(AVG(is_returned) * 100, 2) AS return_rate_pct
        FROM transactions
        GROUP BY product_category
        ORDER BY total_revenue DESC
    """,

    "segment_analysis": """
        SELECT
            c.segment,
            COUNT(DISTINCT c.customer_id) AS customer_count,
            ROUND(SUM(t.final_amount * t.quantity), 2) AS total_revenue,
            ROUND(AVG(t.final_amount), 2) AS avg_order_value,
            ROUND(AVG(c.is_churned) * 100, 2) AS churn_rate_pct
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.segment
        ORDER BY total_revenue DESC
    """,

    "regional_performance": """
        SELECT
            c.region,
            COUNT(DISTINCT c.customer_id) AS total_customers,
            COUNT(t.transaction_id) AS total_orders,
            ROUND(SUM(t.final_amount * t.quantity), 2) AS total_revenue,
            ROUND(AVG(c.is_churned) * 100, 2) AS churn_rate_pct
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.region
        ORDER BY total_revenue DESC
    """,

    "channel_performance": """
        SELECT
            channel,
            COUNT(transaction_id) AS transaction_count,
            ROUND(SUM(final_amount * quantity), 2) AS total_revenue,
            ROUND(AVG(final_amount), 2) AS avg_order_value,
            ROUND(AVG(discount_percent), 2) AS avg_discount,
            ROUND(AVG(rating), 2) AS avg_rating,
            ROUND(AVG(is_returned) * 100, 2) AS return_rate_pct
        FROM transactions
        GROUP BY channel
        ORDER BY total_revenue DESC
    """,

    "top20_customers": """
        SELECT
            c.customer_id, c.age, c.gender, c.segment, c.region,
            COUNT(t.transaction_id) AS total_orders,
            ROUND(SUM(t.final_amount * t.quantity), 2) AS lifetime_value,
            ROUND(AVG(t.rating), 2) AS avg_rating
        FROM customers c
        JOIN transactions t ON c.customer_id = t.customer_id
        WHERE t.is_returned = 0
        GROUP BY c.customer_id
        ORDER BY lifetime_value DESC
        LIMIT 20
    """,

    "payment_method_analysis": """
        SELECT
            payment_method,
            COUNT(transaction_id) AS transaction_count,
            ROUND(SUM(final_amount * quantity), 2) AS total_revenue,
            ROUND(AVG(final_amount), 2) AS avg_value,
            ROUND(AVG(is_returned) * 100, 2) AS return_rate_pct
        FROM transactions
        GROUP BY payment_method
        ORDER BY total_revenue DESC
    """
}


def build_database():
    print(f"Building SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    customers = pd.read_csv(f"{PROCESSED_DIR}/customers_cleaned.csv")
    transactions = pd.read_csv(f"{PROCESSED_DIR}/transactions_cleaned.csv")

    customers.to_sql("customers", conn, if_exists="replace", index=False)
    transactions.to_sql("transactions", conn, if_exists="replace", index=False)

    print(f"  Loaded {len(customers):,} customers and {len(transactions):,} transactions")
    return conn


def run_queries(conn):
    print("\nExecuting SQL analytical queries...")
    results = {}
    for name, query in QUERIES.items():
        df = pd.read_sql_query(query, conn)
        results[name] = df
        output_path = f"{EXPORTS_DIR}/sql_{name}.csv"
        df.to_csv(output_path, index=False)
        print(f"  ✅ {name:35s} → {len(df):,} rows → {output_path}")
    return results


def main():
    print("=" * 60)
    print("  SQL QUERY RUNNER – SQLITE")
    print("=" * 60)
    conn = build_database()
    results = run_queries(conn)
    conn.close()

    print(f"\n  ✅ All query results exported to {EXPORTS_DIR}/")
    print("  ✅ SQLite database saved to data/customer_analytics.db")
    return results


if __name__ == "__main__":
    main()

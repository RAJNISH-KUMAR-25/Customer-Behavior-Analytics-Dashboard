-- ============================================================
-- Customer Behavior Analytics Dashboard
-- SQL Analytical Queries
-- Compatible with: SQLite, PostgreSQL, MySQL, SQL Server
-- ============================================================


-- ──────────────────────────────────────────────────────────
-- 1. DATABASE SCHEMA
-- ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    customer_id     VARCHAR(10) PRIMARY KEY,
    age             INTEGER,
    gender          VARCHAR(10),
    region          VARCHAR(20),
    segment         VARCHAR(20),
    email           VARCHAR(100),
    join_date       DATE,
    loyalty_points  INTEGER,
    is_churned      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   VARCHAR(15) PRIMARY KEY,
    customer_id      VARCHAR(10) REFERENCES customers(customer_id),
    transaction_date DATE,
    product_category VARCHAR(50),
    channel          VARCHAR(20),
    amount           DECIMAL(10,2),
    discount_percent DECIMAL(5,2),
    final_amount     DECIMAL(10,2),
    quantity         INTEGER,
    rating           INTEGER,
    is_returned      INTEGER DEFAULT 0,
    payment_method   VARCHAR(20)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_txn_customer    ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_date        ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_category    ON transactions(product_category);
CREATE INDEX IF NOT EXISTS idx_cust_segment    ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_cust_region     ON customers(region);


-- ──────────────────────────────────────────────────────────
-- 2. EXECUTIVE KPI SUMMARY
-- ──────────────────────────────────────────────────────────

SELECT
    COUNT(DISTINCT c.customer_id)                              AS total_customers,
    COUNT(DISTINCT t.transaction_id)                           AS total_transactions,
    ROUND(SUM(t.final_amount * t.quantity), 2)                 AS total_revenue,
    ROUND(AVG(t.final_amount), 2)                              AS avg_order_value,
    ROUND(AVG(t.rating), 2)                                    AS avg_customer_rating,
    ROUND(AVG(t.is_returned) * 100, 2)                         AS return_rate_pct,
    ROUND(AVG(c.is_churned) * 100, 2)                          AS churn_rate_pct,
    COUNT(DISTINCT CASE WHEN c.segment = 'Premium' THEN c.customer_id END) AS premium_customers
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id;


-- ──────────────────────────────────────────────────────────
-- 3. MONTHLY REVENUE TREND
-- ──────────────────────────────────────────────────────────

SELECT
    STRFTIME('%Y', transaction_date)                   AS year,
    STRFTIME('%m', transaction_date)                   AS month,
    COUNT(transaction_id)                              AS transaction_count,
    ROUND(SUM(final_amount * quantity), 2)             AS revenue,
    ROUND(AVG(final_amount), 2)                        AS avg_order_value,
    ROUND(AVG(rating), 2)                              AS avg_rating,
    ROUND(AVG(is_returned) * 100, 2)                   AS return_rate_pct
FROM transactions
GROUP BY year, month
ORDER BY year, month;


-- ──────────────────────────────────────────────────────────
-- 4. PRODUCT CATEGORY PERFORMANCE
-- ──────────────────────────────────────────────────────────

SELECT
    product_category,
    COUNT(transaction_id)                                   AS total_orders,
    ROUND(SUM(final_amount * quantity), 2)                  AS total_revenue,
    ROUND(AVG(final_amount), 2)                             AS avg_order_value,
    ROUND(AVG(discount_percent), 2)                         AS avg_discount_pct,
    ROUND(AVG(rating), 2)                                   AS avg_rating,
    ROUND(AVG(is_returned) * 100, 2)                        AS return_rate_pct,
    ROUND(SUM(final_amount * quantity) * 100.0 /
          SUM(SUM(final_amount * quantity)) OVER (), 2)      AS revenue_share_pct
FROM transactions
GROUP BY product_category
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 5. CUSTOMER SEGMENTATION ANALYSIS
-- ──────────────────────────────────────────────────────────

SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id)                           AS customer_count,
    ROUND(AVG(c.age), 1)                                    AS avg_age,
    ROUND(AVG(c.loyalty_points), 0)                         AS avg_loyalty_points,
    ROUND(SUM(t.final_amount * t.quantity), 2)              AS total_revenue,
    ROUND(AVG(t.final_amount), 2)                           AS avg_order_value,
    COUNT(t.transaction_id)                                 AS total_transactions,
    ROUND(AVG(c.is_churned) * 100, 2)                       AS churn_rate_pct,
    ROUND(AVG(t.rating), 2)                                 AS avg_rating
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.segment
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 6. CHANNEL PERFORMANCE ANALYSIS
-- ──────────────────────────────────────────────────────────

SELECT
    channel,
    COUNT(transaction_id)                                   AS transaction_count,
    ROUND(SUM(final_amount * quantity), 2)                  AS total_revenue,
    ROUND(AVG(final_amount), 2)                             AS avg_order_value,
    ROUND(AVG(discount_percent), 2)                         AS avg_discount,
    ROUND(AVG(rating), 2)                                   AS avg_rating,
    ROUND(AVG(is_returned) * 100, 2)                        AS return_rate_pct,
    ROUND(COUNT(transaction_id) * 100.0 /
          SUM(COUNT(transaction_id)) OVER (), 2)             AS volume_share_pct
FROM transactions
GROUP BY channel
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 7. RFM ANALYSIS (Recency, Frequency, Monetary)
-- ──────────────────────────────────────────────────────────

WITH rfm_base AS (
    SELECT
        customer_id,
        CAST(JULIANDAY('2025-01-01') -
             JULIANDAY(MAX(transaction_date)) AS INTEGER)    AS recency_days,
        COUNT(transaction_id)                               AS frequency,
        ROUND(SUM(final_amount * quantity), 2)              AS monetary
    FROM transactions
    WHERE is_returned = 0
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC)          AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)              AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)               AS m_score
    FROM rfm_base
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score)                           AS rfm_total,
    CASE
        WHEN (r_score + f_score + m_score) >= 13 THEN 'Champions'
        WHEN (r_score + f_score + m_score) >= 10 THEN 'Loyal Customers'
        WHEN (r_score + f_score + m_score) >= 7  THEN 'Potential Loyalists'
        WHEN (r_score + f_score + m_score) >= 5  THEN 'At Risk'
        ELSE 'Lost'
    END                                                     AS rfm_segment
FROM rfm_scores
ORDER BY rfm_total DESC;


-- ──────────────────────────────────────────────────────────
-- 8. CHURN RISK IDENTIFICATION
-- ──────────────────────────────────────────────────────────

WITH customer_activity AS (
    SELECT
        c.customer_id,
        c.segment,
        c.region,
        c.loyalty_points,
        c.is_churned,
        COUNT(t.transaction_id)                             AS total_transactions,
        MAX(t.transaction_date)                             AS last_purchase_date,
        CAST(JULIANDAY('2025-01-01') -
             JULIANDAY(MAX(t.transaction_date)) AS INTEGER) AS days_since_last_purchase,
        ROUND(AVG(t.rating), 2)                             AS avg_rating
    FROM customers c
    LEFT JOIN transactions t ON c.customer_id = t.customer_id
    GROUP BY c.customer_id
)
SELECT
    customer_id,
    segment,
    region,
    days_since_last_purchase,
    total_transactions,
    avg_rating,
    loyalty_points,
    is_churned,
    CASE
        WHEN days_since_last_purchase > 365 THEN 'High Risk'
        WHEN days_since_last_purchase > 180 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END                                                     AS churn_risk_flag
FROM customer_activity
ORDER BY days_since_last_purchase DESC;


-- ──────────────────────────────────────────────────────────
-- 9. REGIONAL PERFORMANCE
-- ──────────────────────────────────────────────────────────

SELECT
    c.region,
    COUNT(DISTINCT c.customer_id)                           AS total_customers,
    COUNT(t.transaction_id)                                 AS total_orders,
    ROUND(SUM(t.final_amount * t.quantity), 2)              AS total_revenue,
    ROUND(AVG(t.final_amount), 2)                           AS avg_order_value,
    ROUND(AVG(c.is_churned) * 100, 2)                       AS churn_rate_pct,
    ROUND(AVG(t.rating), 2)                                 AS avg_rating
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.region
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 10. TOP 20 HIGH-VALUE CUSTOMERS (CLV Proxy)
-- ──────────────────────────────────────────────────────────

SELECT
    c.customer_id,
    c.age,
    c.gender,
    c.segment,
    c.region,
    c.loyalty_points,
    COUNT(t.transaction_id)                                 AS total_orders,
    ROUND(SUM(t.final_amount * t.quantity), 2)              AS lifetime_value,
    ROUND(AVG(t.final_amount), 2)                           AS avg_order_value,
    ROUND(AVG(t.rating), 2)                                 AS avg_rating,
    MAX(t.transaction_date)                                 AS last_purchase
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.is_returned = 0
GROUP BY c.customer_id
ORDER BY lifetime_value DESC
LIMIT 20;


-- ──────────────────────────────────────────────────────────
-- 11. PAYMENT METHOD ANALYSIS
-- ──────────────────────────────────────────────────────────

SELECT
    payment_method,
    COUNT(transaction_id)                                   AS transaction_count,
    ROUND(SUM(final_amount * quantity), 2)                  AS total_revenue,
    ROUND(AVG(final_amount), 2)                             AS avg_transaction_value,
    ROUND(AVG(discount_percent), 2)                         AS avg_discount,
    ROUND(AVG(is_returned) * 100, 2)                        AS return_rate_pct
FROM transactions
GROUP BY payment_method
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 12. WEEKEND vs WEEKDAY ANALYSIS
-- ──────────────────────────────────────────────────────────

SELECT
    CASE WHEN STRFTIME('%w', transaction_date) IN ('0','6')
         THEN 'Weekend' ELSE 'Weekday' END                  AS day_type,
    COUNT(transaction_id)                                   AS transaction_count,
    ROUND(SUM(final_amount * quantity), 2)                  AS total_revenue,
    ROUND(AVG(final_amount), 2)                             AS avg_order_value,
    ROUND(AVG(rating), 2)                                   AS avg_rating
FROM transactions
GROUP BY day_type
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 13. COHORT RETENTION ANALYSIS (Monthly Cohorts)
-- ──────────────────────────────────────────────────────────

WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(STRFTIME('%Y-%m', transaction_date)) AS cohort_month
    FROM transactions
    GROUP BY customer_id
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        STRFTIME('%Y-%m', t.transaction_date)   AS activity_month,
        COUNT(DISTINCT t.customer_id)           AS active_customers
    FROM transactions t
    JOIN first_purchase f ON t.customer_id = f.customer_id
    GROUP BY f.cohort_month, activity_month
)
SELECT
    cohort_month,
    activity_month,
    active_customers
FROM cohort_activity
ORDER BY cohort_month, activity_month;


-- ──────────────────────────────────────────────────────────
-- 14. OPTIMIZED VIEW: Customer 360
-- ──────────────────────────────────────────────────────────

CREATE VIEW IF NOT EXISTS vw_customer_360 AS
SELECT
    c.customer_id,
    c.age,
    c.gender,
    c.region,
    c.segment,
    c.loyalty_points,
    c.join_date,
    c.is_churned,
    COUNT(t.transaction_id)                                 AS total_orders,
    ROUND(SUM(t.final_amount * t.quantity), 2)              AS lifetime_value,
    ROUND(AVG(t.final_amount), 2)                           AS avg_order_value,
    MAX(t.transaction_date)                                 AS last_purchase_date,
    ROUND(AVG(t.rating), 2)                                 AS avg_rating,
    ROUND(AVG(t.discount_percent), 2)                       AS avg_discount_used
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id;

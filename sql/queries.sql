-- ============================================
-- Customer Behavior Analytics - SQL Queries
-- ============================================

-- 1. Create Tables
CREATE TABLE customers (
    customer_id   VARCHAR(10) PRIMARY KEY,
    age           INT,
    region        VARCHAR(20),
    segment       VARCHAR(20),
    join_date     DATE
);

CREATE TABLE transactions (
    transaction_id VARCHAR(15) PRIMARY KEY,
    customer_id    VARCHAR(10),
    date           DATE,
    category       VARCHAR(30),
    amount         DECIMAL(10,2),
    quantity       INT,
    returned       TINYINT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================
-- KPI QUERIES
-- ============================================

-- 2. Total Revenue & Orders by Month
SELECT
    DATE_FORMAT(date, '%Y-%m') AS month,
    COUNT(transaction_id)      AS total_orders,
    SUM(amount * quantity)     AS total_revenue,
    AVG(amount)                AS avg_order_value
FROM transactions
WHERE returned = 0
GROUP BY month
ORDER BY month;

-- 3. Top 10 Customers by Revenue
SELECT
    c.customer_id,
    c.segment,
    c.region,
    COUNT(t.transaction_id) AS orders,
    SUM(t.amount * t.quantity) AS lifetime_value
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.returned = 0
GROUP BY c.customer_id, c.segment, c.region
ORDER BY lifetime_value DESC
LIMIT 10;

-- 4. Revenue by Category
SELECT
    category,
    COUNT(*) AS transactions,
    SUM(amount * quantity) AS revenue,
    ROUND(AVG(amount), 2) AS avg_amount,
    SUM(returned) AS returns
FROM transactions
GROUP BY category
ORDER BY revenue DESC;

-- 5. Customer Retention by Cohort (Monthly)
SELECT
    DATE_FORMAT(c.join_date, '%Y-%m') AS cohort_month,
    DATE_FORMAT(t.date, '%Y-%m')      AS activity_month,
    COUNT(DISTINCT t.customer_id)     AS active_customers
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY cohort_month, activity_month
ORDER BY cohort_month, activity_month;

-- 6. Churn Risk Customers (No purchase in 180+ days)
SELECT
    customer_id,
    MAX(date) AS last_purchase,
    DATEDIFF(CURDATE(), MAX(date)) AS days_since_purchase,
    COUNT(*) AS total_orders,
    SUM(amount * quantity) AS total_spent
FROM transactions
GROUP BY customer_id
HAVING days_since_purchase > 180
ORDER BY total_spent DESC;

-- 7. Return Rate by Segment
SELECT
    c.segment,
    COUNT(t.transaction_id) AS total_transactions,
    SUM(t.returned) AS returned_orders,
    ROUND(100.0 * SUM(t.returned) / COUNT(*), 2) AS return_rate_pct
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.segment;

-- 8. Optimized Index for Reporting
CREATE INDEX idx_txn_date     ON transactions(date);
CREATE INDEX idx_txn_customer ON transactions(customer_id);
CREATE INDEX idx_txn_category ON transactions(category);

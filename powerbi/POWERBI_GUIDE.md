# Power BI Integration Guide
# Customer Behavior Analytics Dashboard
# ============================================================

## Overview
This folder documents the Power BI integration for the Customer Behavior Analytics project.
The Python pipeline exports analysis-ready CSV files directly consumable by Power BI.

---

## Data Sources (connect these CSVs in Power BI)

| File | Description |
|------|-------------|
| `data/exports/powerbi_daily_revenue.csv` | Daily revenue by category & channel |
| `data/exports/powerbi_customer_profile.csv` | Customer 360 with RFM scores |
| `data/exports/customer_segments.csv` | K-Means cluster assignments |
| `data/exports/churn_predictions.csv` | Churn probability per customer |
| `data/exports/kpi_summary.csv` | Pre-computed KPI values |
| `data/exports/sql_monthly_revenue.csv` | Monthly revenue from SQL analysis |
| `data/exports/sql_category_performance.csv` | Category metrics from SQL |
| `data/exports/sql_channel_performance.csv` | Channel breakdown from SQL |

---

## Recommended Power BI Report Pages

### Page 1: Executive Overview
- Card visuals: Total Revenue, Customers, AOV, Churn Rate
- Line chart: Monthly revenue trend
- Bar chart: Revenue by product category
- Donut chart: Channel mix

### Page 2: Customer Segmentation
- Clustered bar: Customer count by segment
- Scatter: RFM frequency vs monetary colored by segment
- Pie: Churn distribution by segment
- Table: Top 20 customers by lifetime value

### Page 3: Churn & Retention
- KPI card: Overall churn rate
- Gauge: Active vs churned customers
- Bar: Churn rate by region
- Stacked bar: Churn risk distribution (Low / Medium / High)
- Table: High-risk customers

### Page 4: Product & Channel
- Matrix: Revenue by category × channel
- Bar: Return rate by category
- Bar: Average rating by category
- Bar: Payment method distribution

### Page 5: RFM Analysis
- Scatter: Recency vs Monetary (bubble = frequency)
- Bar: RFM segment counts
- Heatmap table: RFM scores by segment

---

## DAX Measures

```dax
-- Total Revenue
Total Revenue = SUMX(transactions, transactions[final_amount] * transactions[quantity])

-- Average Order Value
AOV = AVERAGEX(transactions, transactions[final_amount])

-- Churn Rate
Churn Rate % = DIVIDE(
    COUNTROWS(FILTER(customers, customers[is_churned] = 1)),
    COUNTROWS(customers)
) * 100

-- Return Rate
Return Rate % = DIVIDE(
    COUNTROWS(FILTER(transactions, transactions[is_returned] = 1)),
    COUNTROWS(transactions)
) * 100

-- Revenue MoM Growth
Revenue MoM % = 
VAR CurrentMonth = CALCULATE([Total Revenue], DATESMTD('Date'[Date]))
VAR PrevMonth = CALCULATE([Total Revenue], PREVIOUSMONTH('Date'[Date]))
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth) * 100

-- Customer Lifetime Value
CLV = AVERAGEX(
    VALUES(transactions[customer_id]),
    CALCULATE(SUMX(transactions, transactions[final_amount] * transactions[quantity]))
)

-- High Risk Churn Customers
High Risk Customers = 
COUNTROWS(FILTER(churn_predictions, churn_predictions[churn_risk] = "High Risk"))

-- Active Customers
Active Customers = COUNTROWS(FILTER(customers, customers[is_churned] = 0))

-- Revenue by Segment
Revenue by Segment = 
CALCULATE(
    [Total Revenue],
    ALLEXCEPT(customers, customers[segment])
)
```

---

## Relationships (Star Schema)

```
customers (customer_id) ──< transactions (customer_id)
customers (customer_id) ──< churn_predictions (customer_id)
customers (customer_id) ──< customer_segments (customer_id)
```

---

## Refresh Setup
- Schedule daily refresh from `data/exports/` folder
- Use Power BI Gateway for on-premise file refresh
- Or publish to Power BI Service and use OneDrive/SharePoint sync

---

## Filters / Slicers to Add
- Date range slicer (transaction_date)
- Region slicer
- Segment slicer
- Product category slicer
- Channel slicer
- Churn risk slicer

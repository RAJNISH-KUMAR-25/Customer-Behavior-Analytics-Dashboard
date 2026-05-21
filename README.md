# Customer Behavior Analytics Dashboard

Analyzed 100,000+ customer transaction records to uncover purchasing behavior, trends, and segmentation insights.

## Tech Stack
`Python` `SQL` `Scikit-learn` `Pandas` `Matplotlib` `Excel (openpyxl)` `Power BI`

## Project Structure
```
├── data/
│   └── generate_data.py        # Generates 100K+ synthetic transaction records
├── sql/
│   └── queries.sql             # KPI, retention, churn, and category SQL queries
├── models/
│   └── analytics_models.py     # K-Means segmentation + Random Forest churn model
├── reports/
│   ├── generate_excel_report.py # Builds formatted Excel KPI workbook
│   └── dashboard.png            # Output dashboard image
├── etl_pipeline.py             # Full ETL: load → clean → transform → validate
├── dashboard.py                # Matplotlib analytics dashboard
└── requirements.txt
```

## How to Run

```bash
pip install -r requirements.txt

# Step 1 – Generate data
python data/generate_data.py

# Step 2 – Run ETL
python etl_pipeline.py

# Step 3 – Train models
python models/analytics_models.py

# Step 4 – Generate Excel report
python reports/generate_excel_report.py

# Step 5 – View dashboard
python dashboard.py
```

## Key Features
- **ETL Pipeline** – Data cleaning, validation, and RFM feature engineering
- **Customer Segmentation** – K-Means clustering with silhouette scoring
- **Churn Prediction** – Random Forest classifier with feature importance
- **Excel Reports** – KPI summary, segment analysis, category performance sheets
- **SQL Queries** – Optimized queries with indexes for reporting performance
- **Dashboard** – Interactive multi-panel analytics visualization

"""
main.py
Master orchestration script for Customer Behavior Analytics Dashboard
Runs the full pipeline: Data Generation → ETL → Segmentation → Churn → Dashboard
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.etl.generate_data import main as generate_data
from python.etl.etl_pipeline import run_etl
from python.models.segmentation_model import run_segmentation
from python.models.churn_model import run_churn_model
from python.models.dashboard_report import run_dashboard


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║     CUSTOMER BEHAVIOR ANALYTICS DASHBOARD                ║
║     End-to-End Analytics Pipeline                        ║
║     Python | SQL | Power BI | Scikit-learn | Excel       ║
╚══════════════════════════════════════════════════════════╝
""")


def step(number, title):
    print(f"\n{'─'*60}")
    print(f"  STEP {number}: {title}")
    print(f"{'─'*60}")


def main():
    print_banner()
    start = time.time()

    step(1, "GENERATE SYNTHETIC DATA (100K+ Records)")
    generate_data()

    step(2, "RUN ETL PIPELINE (Extract → Transform → Load)")
    run_etl()

    step(3, "CUSTOMER SEGMENTATION (K-Means Clustering)")
    run_segmentation()

    step(4, "CHURN PREDICTION MODEL (Random Forest)")
    run_churn_model()

    step(5, "GENERATE KPI DASHBOARD REPORTS")
    run_dashboard()

    elapsed = time.time() - start
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅  PIPELINE COMPLETED IN {elapsed:.1f}s
║                                                          ║
║  Output locations:                                       ║
║  📁 data/raw/          → Raw generated datasets          ║
║  📁 data/processed/    → Cleaned & engineered data       ║
║  📁 data/exports/      → Power BI & Excel ready files    ║
║  📁 reports/           → Charts, models & logs           ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()

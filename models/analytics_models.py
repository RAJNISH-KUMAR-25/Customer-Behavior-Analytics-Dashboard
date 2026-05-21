import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, silhouette_score
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 1. CUSTOMER SEGMENTATION (K-Means Clustering)
# ─────────────────────────────────────────────
def customer_segmentation(rfm_path="data/rfm_scores.csv"):
    rfm = pd.read_csv(rfm_path)
    features = rfm[["recency", "frequency", "monetary"]]

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    # Find optimal k
    inertias = []
    for k in range(2, 8):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(scaled)
        inertias.append(km.inertia_)

    # Use k=4
    km = KMeans(n_clusters=4, random_state=42, n_init=10)
    rfm["cluster"] = km.fit_predict(scaled)

    score = silhouette_score(scaled, rfm["cluster"])
    print(f"Silhouette Score: {score:.4f}")

    label_map = {
        rfm.groupby("cluster")["monetary"].mean().idxmax(): "Champions",
        rfm.groupby("cluster")["recency"].mean().idxmin(): "At Risk",
    }
    rfm["segment_label"] = rfm["cluster"].map(label_map).fillna("Regular")

    print("\nCluster Summary:")
    print(rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean().round(2))

    rfm.to_csv("data/segmented_customers.csv", index=False)
    print("Segmentation saved → data/segmented_customers.csv")
    return rfm


# ─────────────────────────────────────────────
# 2. CHURN PREDICTION (Random Forest)
# ─────────────────────────────────────────────
def churn_prediction(rfm_path="data/rfm_scores.csv"):
    rfm = pd.read_csv(rfm_path)

    # Define churn: recency > 180 days = churned
    rfm["churned"] = (rfm["recency"] > 180).astype(int)

    X = rfm[["recency", "frequency", "monetary"]]
    y = rfm["churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("\nChurn Prediction Report:")
    print(classification_report(y_test, y_pred))

    importances = pd.Series(model.feature_importances_, index=X.columns)
    print("\nFeature Importances:")
    print(importances.sort_values(ascending=False))

    rfm["churn_probability"] = model.predict_proba(X)[:, 1]
    rfm.to_csv("data/churn_scores.csv", index=False)
    print("Churn scores saved → data/churn_scores.csv")
    return model, rfm


if __name__ == "__main__":
    print("=" * 40)
    print("  CUSTOMER SEGMENTATION")
    print("=" * 40)
    customer_segmentation()

    print("\n" + "=" * 40)
    print("  CHURN PREDICTION")
    print("=" * 40)
    churn_prediction()

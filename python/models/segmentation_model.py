"""
segmentation_model.py
Customer Segmentation using K-Means Clustering (Scikit-learn)
Features: RFM scores, age, loyalty points, tenure
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import joblib

PROCESSED_DIR = "../../data/processed"
MODELS_DIR = "../../reports"
EXPORTS_DIR = "../../data/exports"

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


def load_data():
    print("Loading processed data...")
    customer_360 = pd.read_csv(f"{PROCESSED_DIR}/customer_360.csv")
    return customer_360


def prepare_features(df: pd.DataFrame):
    print("Preparing features for clustering...")
    features = ["recency", "frequency", "monetary", "age", "loyalty_points", "tenure_days"]
    data = df[features].dropna()
    customer_ids = df.loc[data.index, "customer_id"]

    scaler = StandardScaler()
    scaled = scaler.fit_transform(data)

    print(f"  Feature matrix: {scaled.shape}")
    return scaled, data, customer_ids, scaler, features


def find_optimal_k(scaled_data, k_range=range(2, 9)):
    print("Finding optimal number of clusters (Elbow + Silhouette)...")
    inertias, silhouettes = [], []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(scaled_data)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(scaled_data, labels))
        print(f"  k={k} | Inertia={km.inertia_:.0f} | Silhouette={silhouettes[-1]:.4f}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(list(k_range), inertias, "bo-", linewidth=2)
    axes[0].set_title("Elbow Method – Inertia vs K", fontsize=13)
    axes[0].set_xlabel("Number of Clusters (K)")
    axes[0].set_ylabel("Inertia")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(list(k_range), silhouettes, "rs-", linewidth=2)
    axes[1].set_title("Silhouette Score vs K", fontsize=13)
    axes[1].set_xlabel("Number of Clusters (K)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/cluster_selection.png", dpi=150, bbox_inches="tight")
    plt.close()

    best_k = list(k_range)[np.argmax(silhouettes)]
    print(f"\n  ✅ Optimal K = {best_k} (best silhouette score: {max(silhouettes):.4f})")
    return best_k


def train_kmeans(scaled_data, k=4):
    print(f"\nTraining K-Means with K={k}...")
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=500)
    labels = km.fit_predict(scaled_data)
    score = silhouette_score(scaled_data, labels)
    print(f"  Final Silhouette Score: {score:.4f}")
    return km, labels


def label_clusters(df_with_clusters: pd.DataFrame) -> pd.DataFrame:
    """Map numeric clusters to business-meaningful segment names based on RFM."""
    cluster_means = df_with_clusters.groupby("cluster")[
        ["monetary", "frequency", "recency"]
    ].mean()

    # Rank by monetary spend to assign labels
    cluster_means["rank"] = cluster_means["monetary"].rank(ascending=False).astype(int)
    label_map = {
        row.name: ["High-Value Champions", "Loyal Mid-Tier", "Price-Sensitive Bargain Hunters", "Dormant / At-Risk"][
            min(row["rank"] - 1, 3)
        ]
        for _, row in cluster_means.iterrows()
    }
    df_with_clusters["segment_label"] = df_with_clusters["cluster"].map(label_map)
    return df_with_clusters


def plot_clusters_pca(scaled_data, labels, k):
    print("Generating PCA cluster visualization...")
    pca = PCA(n_components=2, random_state=42)
    reduced = pca.fit_transform(scaled_data)

    fig, ax = plt.subplots(figsize=(10, 7))
    palette = sns.color_palette("Set2", k)
    for i in range(k):
        mask = labels == i
        ax.scatter(reduced[mask, 0], reduced[mask, 1],
                   c=[palette[i]], label=f"Cluster {i}", alpha=0.6, s=15)

    ax.set_title("Customer Segments – PCA Projection", fontsize=14, fontweight="bold")
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    ax.legend(title="Cluster")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/cluster_pca.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {MODELS_DIR}/cluster_pca.png")


def plot_cluster_profiles(df_with_clusters, features):
    print("Generating cluster profile heatmap...")
    profile = df_with_clusters.groupby("cluster")[features].mean()
    profile_norm = (profile - profile.min()) / (profile.max() - profile.min() + 1e-9)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(profile_norm.T, annot=profile.T.round(1), fmt="g",
                cmap="YlOrRd", ax=ax, linewidths=0.5, cbar_kws={"label": "Normalized Score"})
    ax.set_title("Cluster Feature Profiles (Normalized)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Cluster")
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/cluster_profiles.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {MODELS_DIR}/cluster_profiles.png")


def save_outputs(df_with_clusters, km, scaler):
    # Export segmented customer data
    output_path = f"{EXPORTS_DIR}/customer_segments.csv"
    df_with_clusters.to_csv(output_path, index=False)
    print(f"  ✅ Segmented data saved: {output_path}")

    # Save model artifacts
    joblib.dump(km, f"{MODELS_DIR}/kmeans_model.pkl")
    joblib.dump(scaler, f"{MODELS_DIR}/scaler.pkl")
    print(f"  ✅ Model artifacts saved to {MODELS_DIR}/")

    # Cluster summary report
    summary = df_with_clusters.groupby(["cluster", "segment_label"]).agg(
        customer_count=("customer_id", "count"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency", "mean"),
        avg_loyalty=("loyalty_points", "mean")
    ).round(2)
    summary_path = f"{EXPORTS_DIR}/cluster_summary.csv"
    summary.to_csv(summary_path)
    print(f"\nCluster Summary:\n{summary.to_string()}")
    return summary


def run_segmentation():
    print("=" * 60)
    print("  CUSTOMER SEGMENTATION – K-MEANS CLUSTERING")
    print("=" * 60)

    df = load_data()
    scaled_data, feature_data, customer_ids, scaler, features = prepare_features(df)
    best_k = find_optimal_k(scaled_data)
    km, labels = train_kmeans(scaled_data, k=best_k)

    # Merge back
    result_df = feature_data.copy()
    result_df["customer_id"] = customer_ids.values
    result_df["cluster"] = labels
    result_df = label_clusters(result_df)

    # Plots
    plot_clusters_pca(scaled_data, labels, best_k)
    plot_cluster_profiles(result_df, features)

    summary = save_outputs(result_df, km, scaler)

    print("\n" + "=" * 60)
    print("  SEGMENTATION COMPLETE")
    print("=" * 60)
    return result_df, km, summary


if __name__ == "__main__":
    run_segmentation()

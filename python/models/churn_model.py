"""
churn_model.py
Customer Churn Prediction using Random Forest + Logistic Regression
Outputs: churn probabilities, feature importance, evaluation metrics
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

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, precision_recall_curve, average_precision_score
)
import joblib

PROCESSED_DIR = "../../data/processed"
MODELS_DIR = "../../reports"
EXPORTS_DIR = "../../data/exports"

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


def load_data():
    print("Loading data for churn modeling...")
    customer_360 = pd.read_csv(f"{PROCESSED_DIR}/customer_360.csv")
    return customer_360


def engineer_features(df: pd.DataFrame):
    print("Engineering churn features...")
    # Encode categoricals
    le = LabelEncoder()
    df["gender_enc"] = le.fit_transform(df["gender"].fillna("Unknown"))
    df["region_enc"] = le.fit_transform(df["region"].fillna("Unknown"))
    df["segment_enc"] = le.fit_transform(df["segment"].fillna("Regular"))

    feature_cols = [
        "age", "loyalty_points", "tenure_days",
        "recency", "frequency", "monetary", "rfm_score",
        "gender_enc", "region_enc", "segment_enc"
    ]
    target_col = "is_churned"

    model_df = df[feature_cols + [target_col]].dropna()
    X = model_df[feature_cols]
    y = model_df[target_col].astype(int)

    print(f"  Dataset: {X.shape[0]:,} samples | {X.shape[1]} features")
    print(f"  Churn rate: {y.mean():.2%}")
    return X, y, feature_cols


def train_models(X_train, y_train, X_test, y_test, feature_cols):
    print("\nTraining churn prediction models...")
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = {
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=42, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42,
                                                class_weight="balanced", n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                                         learning_rate=0.1, random_state=42)
    }

    results = {}
    for name, model in models.items():
        if name == "Logistic Regression":
            model.fit(X_train_s, y_train)
            y_pred = model.predict(X_test_s)
            y_prob = model.predict_proba(X_test_s)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_prob)
        ap = average_precision_score(y_test, y_prob)
        report = classification_report(y_test, y_pred, output_dict=True)

        results[name] = {
            "model": model,
            "y_pred": y_pred,
            "y_prob": y_prob,
            "auc": auc,
            "ap": ap,
            "report": report
        }
        print(f"\n  [{name}]")
        print(f"    ROC-AUC  : {auc:.4f}")
        print(f"    Avg Prec : {ap:.4f}")
        print(f"    F1 (churn): {report['1']['f1-score']:.4f}")

    return results, scaler


def plot_roc_curves(results, y_test):
    print("\nPlotting ROC curves...")
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#e74c3c", "#2980b9", "#27ae60"]
    for (name, res), color in zip(results.items(), colors):
        fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{name} (AUC={res['auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves – Churn Prediction Models", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/churn_roc_curves.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_feature_importance(rf_result, feature_cols):
    print("Plotting feature importance...")
    rf = rf_result["model"]
    importance_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": rf.feature_importances_
    }).sort_values("Importance", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(importance_df["Feature"], importance_df["Importance"],
                   color=sns.color_palette("Blues_r", len(feature_cols)))
    ax.set_title("Feature Importance – Random Forest Churn Model", fontsize=13, fontweight="bold")
    ax.set_xlabel("Importance Score")
    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/churn_feature_importance.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_confusion_matrix(y_test, y_pred, model_name):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["No Churn", "Churn"],
                yticklabels=["No Churn", "Churn"])
    ax.set_title(f"Confusion Matrix – {model_name}", fontsize=12, fontweight="bold")
    ax.set_ylabel("Actual")
    ax.set_xlabel("Predicted")
    plt.tight_layout()
    safe_name = model_name.lower().replace(" ", "_")
    plt.savefig(f"{MODELS_DIR}/confusion_matrix_{safe_name}.png", dpi=150, bbox_inches="tight")
    plt.close()


def save_churn_predictions(df, X, best_model, scaler, feature_cols, model_name):
    if model_name == "Logistic Regression":
        X_scaled = scaler.transform(X)
        probs = best_model.predict_proba(X_scaled)[:, 1]
    else:
        probs = best_model.predict_proba(X)[:, 1]

    out_df = df.loc[X.index, ["customer_id", "segment", "region", "is_churned"]].copy()
    out_df["churn_probability"] = np.round(probs, 4)
    out_df["churn_risk"] = pd.cut(
        out_df["churn_probability"], bins=[-0.01, 0.3, 0.6, 1.01],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    )
    out_path = f"{EXPORTS_DIR}/churn_predictions.csv"
    out_df.to_csv(out_path, index=False)
    print(f"\n  ✅ Churn predictions saved: {out_path}")
    print(f"\nRisk Distribution:\n{out_df['churn_risk'].value_counts().to_string()}")
    return out_df


def run_churn_model():
    print("=" * 60)
    print("  CUSTOMER CHURN PREDICTION MODEL")
    print("=" * 60)

    df = load_data()
    X, y, feature_cols = engineer_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results, scaler = train_models(X_train, y_train, X_test, y_test, feature_cols)
    best_name = max(results, key=lambda k: results[k]["auc"])
    print(f"\n  🏆 Best model: {best_name} (AUC={results[best_name]['auc']:.4f})")

    plot_roc_curves(results, y_test)
    plot_feature_importance(results["Random Forest"], feature_cols)
    for name, res in results.items():
        plot_confusion_matrix(y_test, res["y_pred"], name)

    best_model = results[best_name]["model"]
    churn_df = save_churn_predictions(df, X, best_model, scaler, feature_cols, best_name)

    # Save best model
    joblib.dump(best_model, f"{MODELS_DIR}/churn_model_best.pkl")

    print("\n" + "=" * 60)
    print("  CHURN MODELING COMPLETE")
    print("=" * 60)
    return results, churn_df


if __name__ == "__main__":
    run_churn_model()

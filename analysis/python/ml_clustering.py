import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

#1. Load raw cycle data 
def load_features(db_path=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cyclesphere.db")
    conn = sqlite3.connect(db_path)

    # Pull all cycle lengths per user — variability computed in pandas (no STDDEV in SQLite)
    cycle_query = """
    SELECT
        user_id,
        CAST(julianday(end_date) - julianday(start_date) AS REAL) AS cycle_length
    FROM cycles
    WHERE end_date IS NOT NULL
    """
    cycles = pd.read_sql(cycle_query, conn)

    profile_query = """
    SELECT
        user_id,
        sleep_hours,
        stress_score_baseline,
        CASE
            WHEN exercise_frequency LIKE '1%' THEN 1
            WHEN exercise_frequency LIKE '3%' THEN 2
            WHEN exercise_frequency LIKE '5%' THEN 3
            ELSE NULL
        END AS exercise_encoded
    FROM users
    """
    profiles = pd.read_sql(profile_query, conn)
    conn.close()

    # Std dev of cycle lengths per user — the correct variability metric
    variability = (
        cycles.groupby("user_id")["cycle_length"]
        .agg(cycle_variability="std", cycle_count="count")
        .reset_index()
    )
    # Drop users with only 1 recorded cycle (std dev undefined)
    variability = variability[variability["cycle_count"] > 1].copy()
    variability["cycle_variability"] = variability["cycle_variability"].fillna(0)

    df = profiles.merge(variability[["user_id", "cycle_variability"]], on="user_id")
    df = df.dropna(subset=["sleep_hours", "stress_score_baseline", "exercise_encoded"])
    return df


FEATURES = ["sleep_hours", "stress_score_baseline", "exercise_encoded", "cycle_variability"]


#2. Choose optimal k via silhouette score 
def select_best_k(X_scaled, k_range=range(2, 7)):
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        scores[k] = silhouette_score(X_scaled, labels)

    best_k = max(scores, key=scores.get)
    return best_k, scores


#3. Fit final model
def fit_kmeans(X_scaled, k):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    return km, labels


#4. PCA visualization — saved as static image
def make_pca_plot(X_scaled, labels, output_path="frontend/pca_clusters.png"):
    pca = PCA(n_components=2, random_state=42)
    X_2d = pca.fit_transform(X_scaled)
    var_explained = pca.explained_variance_ratio_ * 100

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#2ecc71", "#808080"]
    for cluster_id in sorted(set(labels)):
        mask = labels == cluster_id
        ax.scatter(
            X_2d[mask, 0], X_2d[mask, 1],
            c=colors[cluster_id],
            label=f"Cluster {cluster_id}",
            edgecolors="white", linewidths=0.3, s=50, alpha=0.8
        )
    ax.legend(title="Cluster")
    ax.set_xlabel(f"PC1 ({var_explained[0]:.1f}% variance)", fontsize=10)
    ax.set_ylabel(f"PC2 ({var_explained[1]:.1f}% variance)", fontsize=10)
    ax.set_title("KMeans Cluster Distribution (PCA)", fontsize=12)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, dpi=120)
    plt.close(fig)

    total_var = sum(var_explained)
    return output_path, var_explained, total_var


#5. Centroid table
def get_centroid_table(df, labels, scaler, feature_cols=FEATURES):
    df = df.copy()
    df["cluster"] = labels

    # Mean per cluster in original (unscaled) feature space
    centroid_df = df.groupby("cluster")[feature_cols].mean().round(2)
    centroid_df.index = [f"Cluster {i}" for i in centroid_df.index]
    return centroid_df


#Main entry point
def run_clustering(db_path=None, pca_output=None):
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cyclesphere.db")
    if pca_output is None:
        pca_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend", "pca_clusters.png")

    df = load_features(db_path)
    X = df[FEATURES]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k, silhouette_scores = select_best_k(X_scaled)
    km, labels = fit_kmeans(X_scaled, best_k)

    pca_path, var_explained, total_var = make_pca_plot(X_scaled, labels, pca_output)
    centroid_table = get_centroid_table(df, labels, scaler)

    df["cluster"] = labels

    return {
        "df": df,
        "best_k": best_k,
        "silhouette_scores": silhouette_scores,
        "centroid_table": centroid_table,
        "pca_path": pca_path,
        "pca_variance": var_explained,
        "pca_total_variance": total_var,
        "final_silhouette": silhouette_scores[best_k],
    }

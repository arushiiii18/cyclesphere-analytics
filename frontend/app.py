import sys
import os


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
DB_PATH = os.path.join(PROJECT_ROOT, "cyclesphere.db")

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import kruskal

from analysis.python.what_if_engine import simulate_change
from analysis.python.ml_clustering import run_clustering

#Page config
st.set_page_config(page_title="CycleSphere", layout="centered")

st.title("CycleSphere")
st.subheader("Menstrual Health Analytics & Decision Support System")

st.markdown("""
CycleSphere analyzes menstrual cycle data alongside lifestyle factors
to identify **patterns, variability, and focus areas** using SQL, Python,
and explainable analytics.

> This tool provides **data-supported insights only** — not medical advice.
""")


#DB loaders

@st.cache_data
def load_raw_cycles():
    """Raw cycle lengths per user, joined with lifestyle profile."""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        u.user_id,
        u.sleep_hours,
        u.stress_score_baseline,
        u.exercise_frequency,
        CAST(julianday(c.end_date) - julianday(c.start_date) AS REAL) AS cycle_length
    FROM users u
    JOIN cycles c ON u.user_id = c.user_id
    WHERE c.end_date IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data
def load_user_data():
    """
    One row per user. Variability = std dev of cycle lengths (pandas).
    SQLite has no native STDDEV — computed here instead.
    """
    raw = load_raw_cycles()

    variability = (
        raw.groupby("user_id")["cycle_length"]
        .agg(cycle_variability="std", cycle_count="count")
        .reset_index()
    )
    # Drop users with only 1 cycle — std dev is undefined
    variability = variability[variability["cycle_count"] > 1]
    variability["cycle_variability"] = variability["cycle_variability"].fillna(0)

    profile = (
        raw[["user_id", "sleep_hours", "stress_score_baseline", "exercise_frequency"]]
        .drop_duplicates("user_id")
    )

    df = profile.merge(variability[["user_id", "cycle_variability"]], on="user_id")
    return df


@st.cache_data
def load_insight_data():
    """
    Per-user variability (std dev) with lifestyle categories for box plots.
    All categorization done in pandas — no SQLite CASE needed.
    """
    df = load_user_data()

    def categorize_exercise(val):
        if val is None:
            return None
        val = str(val)
        if val.startswith("1"):
            return "Low (1x/week)"
        elif val.startswith("3"):
            return "Moderate (3x/week)"
        elif val.startswith("5"):
            return "High (5x/week)"
        return None

    def categorize_stress(val):
        if val <= 2:
            return "Low Stress"
        elif val == 3:
            return "Moderate Stress"
        else:
            return "High Stress"

    def categorize_sleep(val):
        if val < 6:
            return "Poor (<6h)"
        elif val < 7.5:
            return "Moderate (6-7.5h)"
        else:
            return "Good (7.5h+)"

    df["exercise_category"] = df["exercise_frequency"].apply(categorize_exercise)
    df["stress_category"] = df["stress_score_baseline"].apply(categorize_stress)
    df["sleep_category"] = df["sleep_hours"].apply(categorize_sleep)

    df = df.dropna(subset=["exercise_category"])
    return df


@st.cache_data
def get_user_cycles(user_id):
    """Return all cycle records for a single user, sorted chronologically."""
    conn = sqlite3.connect(DB_PATH)
    query = f"""
    SELECT
        start_date,
        CAST(julianday(end_date) - julianday(start_date) AS REAL) AS cycle_length
    FROM cycles
    WHERE user_id = '{user_id}' AND end_date IS NOT NULL
    ORDER BY start_date ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df["start_date"] = pd.to_datetime(df["start_date"])
    return df


def compute_cycle_prediction(cycles_df):
    """
    Moving average of last 6 cycles + std dev uncertainty window.
    Returns (avg_length, std_dev, estimated_next_date, lower_bound, upper_bound)
    """
    if len(cycles_df) < 2:
        return None, None, None, None, None

    last6 = cycles_df.tail(6)
    avg = last6["cycle_length"].mean()
    std = last6["cycle_length"].std()

    last_start = last6["start_date"].iloc[-1]
    next_date = last_start + pd.to_timedelta(avg, unit="D")
    lower = last_start + pd.to_timedelta(avg - std, unit="D")
    upper = last_start + pd.to_timedelta(avg + std, unit="D")

    return avg, std, next_date, lower, upper


#Scoring helpers

def compute_scores(row):
    sleep = 2 if row["sleep_hours"] < 6 else 1 if row["sleep_hours"] < 7.5 else 0
    stress = 2 if row["stress_score_baseline"] >= 4 else 1 if row["stress_score_baseline"] == 3 else 0
    ex = row["exercise_frequency"]
    exercise = (
        0 if ex is None
        else 2 if str(ex).startswith("1")
        else 1 if str(ex).startswith("3")
        else 0
    )
    return sleep, stress, exercise


def generate_insight_text(sleep_score, stress_score, exercise_score,
                           sleep_hours, stress_val, exercise_val):
    """
    Rule-based natural language insight — fully deterministic, no API needed.
    Every sentence is derived directly from scoring logic.
    """
    lines = []

    # Sleep
    if sleep_score == 2:
        lines.append(
            f"Sleep duration is {sleep_hours:.1f} hours — below the 6-hour risk threshold "
            f"in the scoring model, which is the highest-risk tier."
        )
    elif sleep_score == 1:
        lines.append(
            f"Sleep duration is {sleep_hours:.1f} hours — within the moderate range "
            f"(6–7.5h). Reaching 7.5+ hours would reduce this factor's penalty to zero."
        )
    else:
        lines.append(
            f"Sleep duration is {sleep_hours:.1f} hours — above the 7.5-hour threshold. "
            f"No sleep-related penalty applied."
        )

    # Stress
    if stress_score == 2:
        lines.append(
            f"Baseline stress score is {int(stress_val)} — at or above level 4, "
            f"the highest-risk tier in the scoring model."
        )
    elif stress_score == 1:
        lines.append(
            f"Baseline stress is {int(stress_val)} — moderate level. "
            f"Reducing to level 2 or below would eliminate this factor's penalty."
        )
    else:
        lines.append(
            f"Baseline stress score is {int(stress_val)} — within the low-risk range. "
            f"No stress-related penalty applied."
        )

    # Exercise
    if exercise_score == 2:
        lines.append(
            f"Exercise frequency is low ('{exercise_val}'). "
            f"This is the highest-risk tier for this factor."
        )
    elif exercise_score == 1:
        lines.append(
            f"Exercise frequency is moderate ('{exercise_val}'). "
            f"Increasing to 5+ sessions per week would eliminate this penalty."
        )
    else:
        lines.append(
            f"Exercise frequency is high ('{exercise_val}'). "
            f"No exercise-related penalty applied."
        )

    # Summary
    total = sleep_score + stress_score + exercise_score
    if total == 0:
        lines.append(
            "Total lifestyle penalty score is 0 — all three factors are within "
            "low-risk thresholds. No priority intervention identified."
        )
    else:
        lines.append(
            f"Total lifestyle penalty score: {total}/6. "
            f"Lower scores indicate a lifestyle pattern associated with more stable cycles "
            f"in this dataset."
        )

    return " ".join(lines)


#Kruskal-Wallis helper

def run_kruskal(df, category_col, value_col="cycle_variability"):
    groups = [
        grp[value_col].values
        for _, grp in df.groupby(category_col)
        if len(grp) >= 2
    ]
    if len(groups) < 2:
        return None, None
    stat, p = kruskal(*groups)
    return stat, p


def display_kruskal(p_value, factor_name):
    if p_value is None:
        st.caption("Insufficient data for statistical test.")
        return
    if p_value < 0.05:
        st.caption(
            f"Kruskal-Wallis test: p = {p_value:.4f} — statistically significant difference "
            f"in cycle variability across {factor_name} groups (p < 0.05)."
        )
    else:
        st.caption(
        f"No significant difference found across {factor_name} groups (p = {p_value:.4f}). "
        f"{factor_name} alone may not drive cycle variability — lifestyle factors likely work together rather than independently."
    )


# SECTION 1 — Population Insights
st.header("Lifestyle Insights")
st.markdown(
    f"Cycle variability is measured as the **standard deviation of cycle lengths** per user."
    f"More robust to outliers than range."
)

df_insights = load_insight_data()

# Exercise box plot
st.markdown("**Exercise Frequency vs Cycle Variability**")
exercise_order = ["Low (1x/week)", "Moderate (3x/week)", "High (5x/week)"]
fig_ex = px.box(
    df_insights,
    x="exercise_category",
    y="cycle_variability",
    category_orders={"exercise_category": exercise_order},
    points="all",
    labels={"exercise_category": "Exercise Group", "cycle_variability": "Cycle Variability (std dev, days)"},
    color="exercise_category",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_ex.update_layout(showlegend=False, plot_bgcolor="white")
st.plotly_chart(fig_ex, use_container_width=True)

stat_ex, p_ex = run_kruskal(df_insights, "exercise_category")
display_kruskal(p_ex, "exercise frequency")

# Stress box plot
st.markdown("**Stress Level vs Cycle Variability**")
stress_order = ["Low Stress", "Moderate Stress", "High Stress"]
fig_stress = px.box(
    df_insights,
    x="stress_category",
    y="cycle_variability",
    category_orders={"stress_category": stress_order},
    points="all",
    labels={"stress_category": "Stress Group", "cycle_variability": "Cycle Variability (std dev, days)"},
    color="stress_category",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_stress.update_layout(showlegend=False, plot_bgcolor="white")
st.plotly_chart(fig_stress, use_container_width=True)

stat_st, p_st = run_kruskal(df_insights, "stress_category")
display_kruskal(p_st, "stress level")

# Sleep box plot
st.markdown("**Sleep Duration vs Cycle Variability**")
sleep_order = ["Poor (<6h)", "Moderate (6-7.5h)", "Good (7.5h+)"]
fig_sleep = px.box(
    df_insights,
    x="sleep_category",
    y="cycle_variability",
    category_orders={"sleep_category": sleep_order},
    points="all",
    labels={"sleep_category": "Sleep Group", "cycle_variability": "Cycle Variability (std dev, days)"},
    color="sleep_category",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_sleep.update_layout(showlegend=False, plot_bgcolor="white")
st.plotly_chart(fig_sleep, use_container_width=True)

stat_sl, p_sl = run_kruskal(df_insights, "sleep_category")
display_kruskal(p_sl, "sleep duration")

# Correlation heatmap (collapsible)
with st.expander("How lifestyle factors relate to cycle variability"):
    st.markdown(
        "This chart shows how strongly each lifestyle factor is associated with "
        "cycle variability. Values near 0 mean weak association; values near +1 or -1 "
        "mean strong association. Here, no single factor strongly predicts variability "
        "on its own — which is why we look at lifestyle patterns as a whole."
    )
    st.caption("Near-zero values across the board suggest cycle variability is shaped by combinations of lifestyle factors, not any single one.")
    
    df_corr = load_user_data().copy()
    df_corr["exercise_encoded"] = df_corr["exercise_frequency"].apply(
        lambda x: 1 if str(x).startswith("1") else 2 if str(x).startswith("3") else 3
    )
    
    # select using actual column names, then rename for display
    corr_matrix = df_corr[["sleep_hours", "stress_score_baseline", "exercise_encoded", "cycle_variability"]].corr()
    corr_matrix.columns = ["Sleep Hours", "Stress Score", "Exercise Level", "Cycle Variability"]
    corr_matrix.index = ["Sleep Hours", "Stress Score", "Exercise Level", "Cycle Variability"]

    fig_corr = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        labels={"color": "Pearson r"},
        title="Pearson Correlation Matrix",
    )
    fig_corr.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig_corr, use_container_width=True)

# SECTION 2 — ML Segmentation
st.header("User Segmentation")

with st.spinner("Running clustering pipeline..."):
    clustering = run_clustering()

best_k = clustering["best_k"]
sil_scores = clustering["silhouette_scores"]
centroid_table = clustering["centroid_table"]
pca_path = clustering["pca_path"]
pca_var = clustering["pca_variance"]
final_sil = clustering["final_silhouette"]

st.markdown(
    "KMeans was run for k = 2 through 6. Users were grouped into behavioral profiles based on sleep, stress, "
    "exercise, and cycle variability patterns. The chart below shows how "
    "well-separated these groups are — some overlap is normal with lifestyle data."
)

# Silhouette score bar chart
sil_df = pd.DataFrame({
    "k": list(sil_scores.keys()),
    "Silhouette Score": list(sil_scores.values()),
})
fig_sil = px.bar(
    sil_df, x="k", y="Silhouette Score",
    labels={"k": "Number of Clusters (k)", "Silhouette Score": "Silhouette Score"},
    color_discrete_sequence=["#5B8DB8"],
)
fig_sil.add_vline(x=best_k, line_dash="dot", line_color="red",
                  annotation_text=f"Selected k={best_k}", annotation_position="top right")
fig_sil.update_layout(plot_bgcolor="white")
st.plotly_chart(fig_sil, use_container_width=True)
st.caption(f"k={best_k} groups selected as the most distinct split in this dataset.")

# PCA scatter
if os.path.exists(pca_path):
    st.markdown("**PCA Cluster Visualization**")
    st.image(pca_path, caption=f"2D PCA projection — {pca_var[0]:.1f}% + {pca_var[1]:.1f}% = {sum(pca_var):.1f}% variance explained")

# Centroid table
st.markdown("**User Group Profiles**")
st.markdown(
    "Users are split into two groups based on their lifestyle patterns. "
    "The main difference between groups is exercise frequency — "
    "other factors are similar across both groups in this dataset."
)
centroid_table.columns = ["Sleep (hrs)", "Stress Score", "Exercise Level", "Cycle Variability"]
st.dataframe(centroid_table.style.format("{:.2f}"), use_container_width=True)
st.caption("Clustering is used for pattern discovery only — not diagnosis or prediction.")



# SECTION 3 — Personalized Insights
st.header("Personalized Insights")

df_users = load_user_data()
user_id = st.selectbox("Select a user", df_users["user_id"].unique())
user = df_users[df_users["user_id"] == user_id].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Sleep (hrs)", round(user["sleep_hours"], 1))
col2.metric("Stress Score", int(user["stress_score_baseline"]))
col3.metric("Cycle Variability (std dev)", round(user["cycle_variability"], 2))

#Sparkline + cycle prediction
st.subheader("Next Cycle Estimate")

cycles_df = get_user_cycles(user_id)
avg_len, std_len, next_date, lower_bound, upper_bound = compute_cycle_prediction(cycles_df)

if next_date is not None:
    # Sparkline — last 6 cycles with moving average
    last6 = cycles_df.tail(6).copy()
    last6["moving_avg"] = last6["cycle_length"].expanding().mean()

    fig_spark = go.Figure()
    fig_spark.add_trace(go.Scatter(
        x=last6["start_date"].dt.strftime("%Y-%m-%d"),
        y=last6["cycle_length"],
        mode="lines+markers",
        name="Cycle Length",
        line=dict(color="#5B8DB8", width=2),
        marker=dict(size=6),
    ))
    fig_spark.add_trace(go.Scatter(
        x=last6["start_date"].dt.strftime("%Y-%m-%d"),
        y=last6["moving_avg"],
        mode="lines",
        name="Moving Average",
        line=dict(color="#E07B54", width=2, dash="dot"),
    ))
    fig_spark.update_layout(
        title="Last 6 Recorded Cycle Lengths",
        xaxis_title="Cycle Start Date",
        yaxis_title="Cycle Length (days)",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=280,
        margin=dict(t=40, b=30),
    )
    st.plotly_chart(fig_spark, use_container_width=True)

    # Prediction with uncertainty window
    col_a, col_b = st.columns(2)
    col_a.metric("Estimated Next Start", next_date.strftime("%Y-%m-%d"))
    col_b.metric("Avg Cycle Length (last 6)", f"{avg_len:.1f} days")

    st.info(
        f"Uncertainty window: **{lower_bound.strftime('%Y-%m-%d')}** to **{upper_bound.strftime('%Y-%m-%d')}** "
        f"(±{std_len:.1f} days based on std dev of last 6 cycles)"
    )
    st.caption(
        "Estimate uses a 6-cycle moving average. Uncertainty window = ±1 standard deviation. "
        "Not a medical prediction."
    )
else:
    st.info("Not enough cycle history (minimum 2 cycles required) to generate an estimate.")

#Scoring + rule-based insight
sleep_s, stress_s, exercise_s = compute_scores(user)
total_score = sleep_s + stress_s + exercise_s

scores_dict = {"Sleep": sleep_s, "Stress": stress_s, "Exercise": exercise_s}
max_score = max(scores_dict.values())
focus = [k for k, v in scores_dict.items() if v == max_score and v > 0]
primary_focus = "Balanced — no high-risk factors identified" if not focus else ", ".join(focus)

st.subheader("Primary Focus Area")
st.info(primary_focus)

st.subheader("Lifestyle Insight")
insight_text = generate_insight_text(
    sleep_s, stress_s, exercise_s,
    user["sleep_hours"], user["stress_score_baseline"], user["exercise_frequency"]
)
st.markdown(insight_text)
st.caption(
    "Insight generated directly from the rule-based scoring model — fully deterministic, "
    "no external API. Higher scores = higher lifestyle risk in this model."
)


# SECTION 4 — What-If Scenario Analysis
st.header("What-If Scenario Analysis")

scenario = st.radio(
    "Simulate a small lifestyle change:",
    ["Improve Sleep (+1 hour)", "Reduce Stress (-1 level)", "Increase Exercise (+1 level)"]
)

change_map = {
    "Improve Sleep (+1 hour)": "sleep",
    "Reduce Stress (-1 level)": "stress",
    "Increase Exercise (+1 level)": "exercise",
}

result = simulate_change(user, change_map[scenario])

before_score = total_score
after_score = result["total_penalty_score"]

col1, col2 = st.columns(2)
col1.metric("Current Risk Score", before_score, help="Sum of sleep + stress + exercise penalty scores (0–6)")
col2.metric("Simulated Risk Score", after_score, delta=after_score - before_score,
            delta_color="inverse")

# Per-factor breakdown bar chart (before vs after)
# floor at 0.01 so zero-risk factors still render visibly
before_factors = {"Sleep": max(sleep_s, 0.01), "Stress": max(stress_s, 0.01), "Exercise": max(exercise_s, 0.01)}
after_factors = {
    "Sleep": max(result["sleep_score"], 0.01),
    "Stress": max(result["stress_score"], 0.01),
    "Exercise": max(result["exercise_score"], 0.01),
}

factor_df = pd.DataFrame({
    "Factor": list(before_factors.keys()) * 2,
    "Score": list(before_factors.values()) + list(after_factors.values()),
    "Scenario": ["Before"] * 3 + ["After (Simulated)"] * 3,
})

fig_whatif = px.bar(
    factor_df, x="Factor", y="Score", color="Scenario",
    barmode="group",
    color_discrete_map={"Before": "#c0392b", "After (Simulated)": "#27ae60"},
    labels={"Score": "Penalty Score (0 = no risk, 2 = high risk)", "Factor": "Lifestyle Factor"},
    title="Before vs After Penalty Score by Factor",
    range_y=[0, 2.5],
)
fig_whatif.update_layout(plot_bgcolor="white")
st.plotly_chart(fig_whatif, use_container_width=True)

if after_score < before_score:
    st.success(f"This change reduces your risk score from {before_score} to {after_score}.")
elif after_score == before_score:
    st.warning("This change doesn't impact the risk score — this factor may already be at a lower-risk level for this user.")
else:
    st.warning("No further improvement possible — this factor is already at its lowest risk level.")

st.caption("Results are based on the scoring model only and not clinical guidance.")

#Footer
st.markdown("---")
st.caption("CycleSphere  •  SQL  •  Python  •  Explainable ML  •  Scenario-Based Analytics")
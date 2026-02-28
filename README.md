# CycleSphere — Menstrual Health Analytics Platform

A data-driven analytics platform that studies relationships between lifestyle factors (sleep, stress, exercise) and menstrual cycle variability across 2,000 users and 17,976 cycle records.

> This tool provides data-supported insights only — not medical advice.

**[Live Demo](https://cyclesphere-analytics-yvhtyqq2z72gjcbbem32e4.streamlit.app/)**

---

## What It Does

- Analyzes how sleep, stress, and exercise relate to cycle variability using SQL and pandas
- Segments users into behavioral profiles using KMeans clustering (silhouette-optimized)
- Generates personalized, rule-based lifestyle insights with transparent scoring logic
- Predicts next cycle start date with a statistical uncertainty window
- Simulates lifestyle changes via a what-if scenario engine

---

## Architecture

```
Period_Log.csv + User_Profile.csv
        │
        ▼
ETL Pipeline (pandas) — clean, derive, transform
        │
        ▼
SQLite Database (users + cycles tables)
        │
        ▼
SQL queries + pandas analysis + ML pipeline
        │
        ▼
Streamlit Dashboard (frontend/app.py)
```

---

## Key Findings

- No single lifestyle factor shows a statistically significant effect on cycle variability in isolation (Kruskal-Wallis p > 0.05 across all three factors)
- KMeans clustering (k=2, silhouette-optimized) splits users primarily by exercise frequency
- Near-zero Pearson correlations across all features confirm variability is driven by multi-factor lifestyle patterns, not individual variables

---

## Tech Stack

| Tool | Why |
|------|-----|
| Python + pandas | ETL pipeline, std dev variability computation (SQLite has no STDDEV) |
| SQLite + SQL | Relational schema, analytical queries, date arithmetic via julianday() |
| Scikit-learn | KMeans clustering, StandardScaler, PCA, silhouette score |
| SciPy | Kruskal-Wallis non-parametric statistical testing |
| Plotly | Interactive box plots, correlation heatmap, what-if charts |
| Streamlit | Interactive dashboard frontend |
| Matplotlib | Static PCA cluster visualization |

---

## How to Run Locally

```bash
# Clone the repo
git clone https://github.com/arushiiii18/cyclesphere-analytics.git
cd cyclesphere-analytics

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run frontend/app.py
```

---

## Project Structure

```
├── analysis/
│   ├── python/
│   │   ├── ml_clustering.py      # KMeans + PCA + silhouette
│   │   ├── what_if_engine.py     # scenario simulation
│   │   ├── decision_engine.py    # rule-based scoring
│   │   └── variability_engine.py # std dev computation
│   └── sql/
│       └── cycle_analysis.sql
├── data/raw/
│   ├── Period_Log.csv
│   └── User_Profile.csv
├── frontend/
│   └── app.py                    # Streamlit dashboard
├── cyclesphere.db                # SQLite database
├── schema.md                     # Database schema documentation
└── requirements.txt
```

---

## Limitations

- Lifestyle data is self-reported and stored as static user-level baselines — short-term fluctuations not captured
- No medical claims made — system is scoped strictly to pattern analytics
- Cycle variability clusters show overlap due to nature of self-reported lifestyle data
- Statistical tests returned null results — displayed explicitly, not hidden

---

## Dataset

External menstrual health dataset mapped to a normalized SQLite schema via ETL pipeline. Medical, hormonal, and diagnostic columns excluded to maintain non-diagnostic scope.
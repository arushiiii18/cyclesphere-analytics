# CycleSphere Database Schema

## Actual Table Structure

> **Note:** The `lifestyle_logs` and `recommendations` tables exist in `create_tables.sql`
> but are **not used** in the current pipeline. Lifestyle features (sleep, stress, exercise)
> are stored directly on the `users` table, sourced from the external dataset during ETL.
> This is documented here for transparency.

---

## 1. users
Stores one row per user with baseline lifestyle metrics from the ingested dataset.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | TEXT | PRIMARY KEY | Unique user identifier |
| age | INTEGER | NOT NULL | User age |
| sleep_hours | REAL | — | Average daily sleep duration |
| exercise_frequency | TEXT | — | Categorical: e.g. "1–2 days/week", "3–4 days/week", "5+ days/week" |
| diet_quality | TEXT | — | Self-reported diet quality |
| stress_score_baseline | INTEGER | — | Baseline stress score (1–5 scale) |

---

## 2. cycles
Stores individual menstrual cycle records per user.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| cycle_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique cycle identifier |
| user_id | TEXT | FOREIGN KEY → users(user_id) | Cycle owner |
| start_date | DATE | NOT NULL | Cycle start date |
| end_date | DATE | NOT NULL | Cycle end date |
| prev_cycle_length | INTEGER | — | Length of the previous cycle (from source data) |

---

## 3. symptoms
Stores symptom records per cycle (populated but not used in primary analysis pipeline).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| symptom_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique symptom record |
| cycle_id | INTEGER | FOREIGN KEY → cycles(cycle_id) | Related cycle |
| symptom_name | TEXT | NOT NULL | Symptom label |
| severity | INTEGER | CHECK (1–5) | Severity rating |

---

## 4. lifestyle_logs
Defined in schema but **not currently populated** — lifestyle data is stored on `users` instead.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| log_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique log entry |
| user_id | TEXT | FOREIGN KEY → users(user_id) | User |
| log_date | DATE | NOT NULL | Date of log |
| sleep_hours | REAL | CHECK (0–24) | Daily sleep |
| exercise_minutes | INTEGER | CHECK (>= 0) | Exercise duration |
| stress_level | INTEGER | CHECK (1–5) | Daily stress rating |

**Why not populated:** The external dataset provides lifestyle data as static user-level
aggregates (average sleep, baseline stress, exercise frequency), not as time-series daily logs.
Migrating to daily lifestyle logs is a future enhancement.

---

## Key Design Decisions

- Cycle variability is **not stored** — it is derived at query time as the standard deviation
  of cycle lengths per user using pandas (SQLite has no native STDDEV function).
- Cycle length is **not stored** directly — it is derived from `start_date` and `end_date`
  using `julianday()` arithmetic in SQL.
- Lifestyle features are stored at the user level (not daily) because the source dataset
  provides aggregate self-reported values, not time-series observations.

---

## Data Flow

```
Period_Log.csv + User_Profile.csv
        │
        ▼
    ETL Pipeline (data_transform_load.py)
        │  — extract, clean, derive end_date, standardize dtypes
        ▼
    cyclesphere.db  (users + cycles tables)
        │
        ▼
    SQL analytical queries  →  pandas validation  →  Python analysis modules
        │
        ▼
    Streamlit dashboard (app.py)
```

---

## Limitations

- Lifestyle data is self-reported and stored as static baseline values per user.
  Short-term fluctuations are not captured.
- No time-series daily log data is currently available for per-cycle lifestyle correlation.
- Sample size affects statistical test power — null Kruskal-Wallis results should be
  interpreted carefully given dataset size.





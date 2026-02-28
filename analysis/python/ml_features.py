import sqlite3
import pandas as pd

# 1. Connect to DB
conn = sqlite3.connect("cyclesphere.db")

# 2. SQL: user-level feature table
query = """
SELECT
    u.user_id,
    u.sleep_hours,
    u.stress_score_baseline,
    u.exercise_frequency,
    MAX(julianday(c.end_date) - julianday(c.start_date)) -
    MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
FROM users u
JOIN cycles c
    ON u.user_id = c.user_id
GROUP BY u.user_id;
"""

df = pd.read_sql(query, conn)
conn.close()

# 3. Encode exercise frequency
exercise_map = {
    "1–2 days/week": 1,
    "3–4 days/week": 2,
    "5–6 days/week": 3
}

df["exercise_encoded"] = df["exercise_frequency"].map(exercise_map)

# 4. Drop unusable rows
df = df.dropna(subset=[
    "sleep_hours",
    "stress_score_baseline",
    "exercise_encoded",
    "cycle_variability"
])


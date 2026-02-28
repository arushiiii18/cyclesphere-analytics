import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cyclesphere.db")

# 1. Connect to DB
conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    u.user_id,
    u.sleep_hours,
    u.stress_score_baseline,
    u.exercise_frequency,
    MAX(julianday(c.end_date) - julianday(c.start_date)) -
    MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
FROM users u
JOIN cycles c ON u.user_id = c.user_id
GROUP BY u.user_id;
"""

df = pd.read_sql(query, conn)
conn.close()
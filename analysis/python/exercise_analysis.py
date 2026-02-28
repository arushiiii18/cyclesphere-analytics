import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Connect to DB
conn = sqlite3.connect("cyclesphere.db")

# 2. SQL query (exclude unknowns)
query = """
SELECT
    CASE
        WHEN exercise_frequency LIKE '1%' THEN 'low_exercise'
        WHEN exercise_frequency LIKE '3%' THEN 'moderate_exercise'
        WHEN exercise_frequency LIKE '5%' THEN 'high_exercise'
        ELSE 'unknown'
    END AS exercise_category,
    AVG(cycle_variability) AS avg_cycle_variability
FROM (
    SELECT
        u.user_id,
        u.exercise_frequency,
        MAX(julianday(c.end_date) - julianday(c.start_date)) -
        MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
    FROM users u
    JOIN cycles c
        ON u.user_id = c.user_id
    GROUP BY u.user_id
)
WHERE exercise_category != 'unknown'
GROUP BY exercise_category;
"""

df = pd.read_sql(query, conn)
conn.close()

print(df)

# 3. Plot
plt.figure()
plt.bar(df["exercise_category"], df["avg_cycle_variability"])
plt.xlabel("Exercise Frequency")
plt.ylabel("Average Cycle Variability (days)")
plt.title("Exercise Frequency vs Cycle Variability")
plt.show()

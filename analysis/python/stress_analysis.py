import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Connect to DB
conn = sqlite3.connect("cyclesphere.db")

# 2. SQL query
query = """
SELECT
    CASE
        WHEN stress_score_baseline <= 2 THEN 'low_stress'
        WHEN stress_score_baseline = 3 THEN 'moderate_stress'
        ELSE 'high_stress'
    END AS stress_category,
    AVG(cycle_variability) AS avg_cycle_variability
FROM (
    SELECT
        u.user_id,
        u.stress_score_baseline,
        MAX(julianday(c.end_date) - julianday(c.start_date)) -
        MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
    FROM users u
    JOIN cycles c
        ON u.user_id = c.user_id
    GROUP BY u.user_id
)
GROUP BY stress_category;
"""

df = pd.read_sql(query, conn)
conn.close()

print(df)

# 3. Plot
plt.figure()
plt.bar(df["stress_category"], df["avg_cycle_variability"])
plt.xlabel("Stress Category")
plt.ylabel("Average Cycle Variability (days)")
plt.title("Stress Level vs Cycle Variability")
plt.show()

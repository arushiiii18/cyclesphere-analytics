import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Connect to DB
conn = sqlite3.connect("cyclesphere.db")

# 2. SQL query
query = """
SELECT
    CASE
        WHEN sleep_hours < 6 THEN 'low_sleep'
        WHEN sleep_hours BETWEEN 6 AND 7.5 THEN 'moderate_sleep'
        ELSE 'good_sleep'
    END AS sleep_category,
    AVG(cycle_variability) AS avg_cycle_variability
FROM (
    SELECT
        u.user_id,
        u.sleep_hours,
        MAX(julianday(c.end_date) - julianday(c.start_date)) -
        MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
    FROM users u
    JOIN cycles c
        ON u.user_id = c.user_id
    GROUP BY u.user_id
)
GROUP BY sleep_category;
"""

df = pd.read_sql(query, conn)
conn.close()

print(df)

# 3. Plot
plt.figure()
plt.bar(df["sleep_category"], df["avg_cycle_variability"])
plt.xlabel("Sleep Category")
plt.ylabel("Average Cycle Variability (days)")
plt.title("Sleep Duration vs Cycle Variability")
plt.show()

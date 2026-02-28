import sqlite3
import pandas as pd

# connect to database
conn = sqlite3.connect("cyclesphere.db")

# query: average cycle length
query = """
SELECT
    user_id,
    AVG(julianday(end_date) - julianday(start_date)) AS avg_cycle_length
FROM cycles
WHERE end_date IS NOT NULL
GROUP BY user_id;
"""

df = pd.read_sql(query, conn)
print("Average cycle length per user:")
print(df)


# validation: symptom severity vs cycle regularity
query = """
WITH cycle_lengths AS (
    SELECT
        user_id,
        (julianday(end_date) - julianday(start_date)) AS cycle_length
    FROM cycles
    WHERE end_date IS NOT NULL
),
user_variance AS (
    SELECT
        user_id,
        AVG(cycle_length * cycle_length)
        - AVG(cycle_length) * AVG(cycle_length) AS variance
    FROM cycle_lengths
    GROUP BY user_id
),
user_regularity AS (
    SELECT
        user_id,
        CASE
            WHEN variance <= 4 THEN 'Regular'
            ELSE 'Irregular'
        END AS regularity_label
    FROM user_variance
)
SELECT
    ur.regularity_label,
    AVG(s.severity) AS avg_symptom_severity
FROM user_regularity ur
JOIN cycles c ON ur.user_id = c.user_id
JOIN symptoms s ON c.cycle_id = s.cycle_id
GROUP BY ur.regularity_label;
"""

df_symptom_reg = pd.read_sql(query, conn)
print("\nSymptom severity vs cycle regularity:")
print(df_symptom_reg)

# validation: sleep vs symptom severity
query = """
SELECT
    u.user_id,
    AVG(l.sleep_hours) AS avg_sleep_hours,
    AVG(s.severity) AS avg_symptom_severity
FROM users u
JOIN lifestyle_logs l ON u.user_id = l.user_id
JOIN cycles c ON u.user_id = c.user_id
JOIN symptoms s ON c.cycle_id = s.cycle_id
GROUP BY u.user_id;
"""

df_sleep = pd.read_sql(query, conn)
print("\nSleep vs symptom severity:")
print(df_sleep)


import matplotlib.pyplot as plt

plt.bar(
    df_symptom_reg['regularity_label'],
    df_symptom_reg['avg_symptom_severity']
)
plt.xlabel("Cycle Regularity")
plt.ylabel("Average Symptom Severity")
plt.title("Symptom Severity by Cycle Regularity")
plt.tight_layout()
plt.show()

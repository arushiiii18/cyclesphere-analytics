-- Query 1: Average cycle length per user
SELECT
    user_id,
    AVG(julianday(end_date) - julianday(start_date)) AS avg_cycle_length_days
FROM cycles
WHERE end_date IS NOT NULL
GROUP BY user_id;


-- Query 2: Cycle regularity (variance)
WITH cycle_lengths AS (
    SELECT
        user_id,
        (julianday(end_date) - julianday(start_date)) AS cycle_length
    FROM cycles
    WHERE end_date IS NOT NULL
)
SELECT
    user_id,
    AVG(cycle_length) AS avg_cycle_length,
    AVG(cycle_length * cycle_length) - AVG(cycle_length) * AVG(cycle_length) AS variance
FROM cycle_lengths
GROUP BY user_id;


-- Cycle regularity (variance) after introducing controlled irregularity
SELECT cycle_id, user_id, start_date, end_date,
       (julianday(end_date) - julianday(start_date)) AS cycle_length
FROM cycles
WHERE user_id = 1;

--Query 3: User-level Regularity Classification

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
)
SELECT
    user_id,
    variance,
    CASE
        WHEN variance <= 4 THEN 'Regular'
        ELSE 'Irregular'
    END AS cycle_regularity_label
FROM user_variance;

--Query 4: Average Symptom Severity per User
SELECT
    c.user_id,
    AVG(s.severity) AS avg_symptom_severity
FROM symptoms s
JOIN cycles c
    ON s.cycle_id = c.cycle_id
GROUP BY c.user_id;

--Query 5: Symptom Severity vs Cycle Regularity
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
JOIN cycles c
    ON ur.user_id = c.user_id
JOIN symptoms s
    ON c.cycle_id = s.cycle_id
GROUP BY ur.regularity_label;

--Query 6: Average sleep vs average symptom severity (per user)
SELECT
    u.user_id,
    AVG(l.sleep_hours) AS avg_sleep_hours,
    AVG(s.severity) AS avg_symptom_severity
FROM users u
JOIN lifestyle_logs l
    ON u.user_id = l.user_id
JOIN cycles c
    ON u.user_id = c.user_id
JOIN symptoms s
    ON c.cycle_id = s.cycle_id
GROUP BY u.user_id;

--Query 7: Stress Level vs Cycle Regularity
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
),
user_stress AS (
    SELECT
        user_id,
        AVG(stress_level) AS avg_stress_level
    FROM lifestyle_logs
    GROUP BY user_id
)
SELECT
    ur.regularity_label,
    AVG(us.avg_stress_level) AS avg_stress_level
FROM user_regularity ur
JOIN user_stress us
    ON ur.user_id = us.user_id
GROUP BY ur.regularity_label;






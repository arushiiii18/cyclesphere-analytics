--Cycle Regularity Analysis

-- A1: Derive cycle length from dates
SELECT
    user_id,
    start_date,
    end_date,
    julianday(end_date) - julianday(start_date) AS cycle_length_days
FROM cycles
LIMIT 10;


-- A2: Average cycle length per user
SELECT
    user_id,
    ROUND(AVG(julianday(end_date) - julianday(start_date)), 2) AS avg_cycle_length
FROM cycles
GROUP BY user_id;


-- A3: Cycle regularity (range-based)
SELECT
    user_id,
    ROUND(
        MAX(julianday(end_date) - julianday(start_date)) -
        MIN(julianday(end_date) - julianday(start_date)),
        2
    ) AS cycle_length_range
FROM cycles
GROUP BY user_id;


-- A4: Rule-based cycle classification
SELECT
    user_id,
    COUNT(*) AS total_cycles,
    ROUND(
        MAX(julianday(end_date) - julianday(start_date)) -
        MIN(julianday(end_date) - julianday(start_date)),
        2
    ) AS cycle_length_range,
    CASE
        WHEN (
            MAX(julianday(end_date) - julianday(start_date)) -
            MIN(julianday(end_date) - julianday(start_date))
        ) > 7
        THEN 'irregular'
        ELSE 'regular'
    END AS cycle_type
FROM cycles
GROUP BY user_id;

-- Sleep Duration vs Cycle Regularity
-- A6.1 + A6.2: Per-user variability aggregated by sleep category
SELECT
    CASE
        WHEN sleep_hours < 6 THEN 'low_sleep'
        WHEN sleep_hours BETWEEN 6 AND 7.5 THEN 'moderate_sleep'
        ELSE 'good_sleep'
    END AS sleep_category,
    COUNT(user_id) AS users_count,
    ROUND(AVG(cycle_variability), 2) AS avg_cycle_variability
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

-- Stress level vs cycle regularity
SELECT
    u.user_id,
    u.stress_score_baseline,
    MAX(julianday(c.end_date) - julianday(c.start_date)) -
    MIN(julianday(c.end_date) - julianday(c.start_date)) AS cycle_variability
FROM users u
JOIN cycles c
    ON u.user_id = c.user_id
GROUP BY u.user_id;

-- --1–2 → low_stress
-- 3 → moderate_stress
-- 4–5 → high_stress
SELECT
    CASE
        WHEN stress_score_baseline <= 2 THEN 'low_stress'
        WHEN stress_score_baseline = 3 THEN 'moderate_stress'
        ELSE 'high_stress'
    END AS stress_category,
    COUNT(user_id) AS users_count,
    ROUND(AVG(cycle_variability), 2) AS avg_cycle_variability
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

-- Exercise frequency vs cycle regularity(pattern based normalization)
SELECT
    CASE
        WHEN exercise_frequency LIKE '1%' THEN 'low_exercise'
        WHEN exercise_frequency LIKE '3%' THEN 'moderate_exercise'
        WHEN exercise_frequency LIKE '5%' THEN 'high_exercise'
        ELSE 'unknown'
    END AS exercise_category,
    COUNT(user_id) AS users_count,
    ROUND(AVG(cycle_variability), 2) AS avg_cycle_variability
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
GROUP BY exercise_category;

-- NOTE: 'unknown' category excluded from final visual analysis due to ambiguity




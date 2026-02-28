INSERT INTO users (user_id, age, created_at) VALUES
(1, 21, '2024-01-01'),
(2, 25, '2024-02-10');

INSERT INTO cycles (cycle_id, user_id, start_date, end_date) VALUES
(1, 1, '2024-01-05', '2024-01-31'),
(2, 1, '2024-02-03', '2024-02-29'),
(3, 1, '2024-03-04', '2024-03-30'),

(4, 2, '2024-02-15', '2024-03-12'),
(5, 2, '2024-03-16', '2024-04-11');

SELECT * FROM users;
SELECT * FROM cycles;

UPDATE cycles
SET end_date = '2024-03-05'
WHERE cycle_id = 2;

INSERT INTO symptoms (symptom_id, cycle_id, symptom_name, severity) VALUES
-- User 1 (irregular)
(1, 1, 'Cramps', 3),
(2, 1, 'Fatigue', 2),

(3, 2, 'Cramps', 5),
(4, 2, 'Fatigue', 4),

(5, 3, 'Cramps', 3),

-- User 2 (regular)
(6, 4, 'Cramps', 2),
(7, 4, 'Fatigue', 2),

(8, 5, 'Cramps', 2);

SELECT * FROM symptoms;

INSERT INTO lifestyle_logs (log_id, user_id, log_date, sleep_hours, exercise_minutes, stress_level) VALUES
-- User 1 (irregular cycles, higher stress)
(1, 1, '2024-01-10', 5.5, 10, 4),
(2, 1, '2024-02-10', 6.0, 0, 5),
(3, 1, '2024-03-10', 5.0, 15, 4),

-- User 2 (regular cycles, more stable lifestyle)
(4, 2, '2024-02-20', 7.5, 30, 2),
(5, 2, '2024-03-20', 8.0, 25, 2);

SELECT * FROM lifestyle_logs;







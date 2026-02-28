DROP TABLE IF EXISTS lifestyle_logs;
DROP TABLE IF EXISTS symptoms;
DROP TABLE IF EXISTS cycles;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    sleep_hours REAL,
    exercise_frequency TEXT,
    diet_quality TEXT,
    stress_score_baseline INTEGER
);

CREATE TABLE cycles (
    cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    prev_cycle_length INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE symptoms (
    symptom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id INTEGER NOT NULL,
    symptom_name TEXT NOT NULL,
    severity INTEGER CHECK (severity BETWEEN 1 AND 5),
    FOREIGN KEY (cycle_id) REFERENCES cycles(cycle_id)
);

CREATE TABLE lifestyle_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    log_date DATE NOT NULL,
    sleep_hours REAL CHECK (sleep_hours BETWEEN 0 AND 24),
    exercise_minutes INTEGER CHECK (exercise_minutes >= 0),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 5),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);



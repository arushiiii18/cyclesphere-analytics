import pandas as pd
import sqlite3

# 1. Connect to database
DB_PATH = "cyclesphere.db"
conn = sqlite3.connect(DB_PATH)
print("Connected to database")

# 2. Load raw datasets
df_user_raw = pd.read_csv("data/raw/User_Profile.csv")
df_period_raw = pd.read_csv("data/raw/Period_Log.csv")
print("Raw data loaded")

# 3. USER table transform
df_users = df_user_raw[
    [
        "user_id",
        "age",
        "sleep_hours",
        "exercise_frequency",
        "diet_quality",
        "stress_score_baseline"
    ]
].copy()

# user_id is TEXT like U00001 ,keeping it as TEXT
df_users["user_id"] = df_users["user_id"].astype(str)

df_users["age"] = pd.to_numeric(df_users["age"], errors="coerce").astype("Int64")
df_users["sleep_hours"] = pd.to_numeric(df_users["sleep_hours"], errors="coerce")
df_users["stress_score_baseline"] = (
    pd.to_numeric(df_users["stress_score_baseline"], errors="coerce")
    .fillna(0)
    .astype(int)
)

df_users["exercise_frequency"] = df_users["exercise_frequency"].astype(str).str.lower()
df_users["diet_quality"] = df_users["diet_quality"].astype(str).str.lower()

print("User data transformed")

# 4. CYCLES table transform
df_cycles = df_period_raw[
    [
        "user_id",
        "start_date",
        "cycle_length_days",
        "prev_cycle_length"
    ]
].copy()

df_cycles["user_id"] = df_cycles["user_id"].astype(str)

df_cycles["start_date"] = pd.to_datetime(df_cycles["start_date"], errors="coerce")

# derive end_date
df_cycles["end_date"] = df_cycles["start_date"] + pd.to_timedelta(
    df_cycles["cycle_length_days"], unit="D"
)

# DROP derived column before insert
df_cycles = df_cycles[
    ["user_id", "start_date", "end_date", "prev_cycle_length"]
]

print("Cycle data transformed")
# 5. Insert into database
# Insert users ONLY if table is empty
existing_users = pd.read_sql("SELECT COUNT(*) as cnt FROM users", conn)

if existing_users["cnt"][0] == 0:
    df_users.to_sql("users", conn, if_exists="append", index=False)
    print("Users inserted")
else:
    print("Users already exist, skipping user insert")

df_cycles.to_sql("cycles", conn, if_exists="append", index=False)
print("Cycles inserted")

print("Data inserted successfully")
conn.close()

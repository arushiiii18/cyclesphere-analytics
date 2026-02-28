import pandas as pd

# load raw datasets (CSV, not Excel)
df_user = pd.read_csv("data/raw/User_Profile.csv")
df_period = pd.read_csv("data/raw/Period_Log.csv")

print("USER PROFILE COLUMNS:")
print(df_user.columns.tolist())

print("\nPERIOD LOG COLUMNS:")
print(df_period.columns.tolist())

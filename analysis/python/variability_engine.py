import sqlite3
import pandas as pd

def compute_user_variability(db_path="cyclesphere.db"):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT
        user_id,
        julianday(end_date) - julianday(start_date) AS cycle_length
    FROM cycles
    WHERE end_date IS NOT NULL
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Proper variability = std dev of cycle lengths per user
    variability = df.groupby("user_id")["cycle_length"].agg(
        cycle_variability="std",      # standard deviation
        avg_cycle_length="mean",
        cycle_count="count",
        cycle_range=lambda x: x.max() - x.min()  # keep range for comparison
    ).reset_index()
    
    # drop users with only 1 cycle (std dev is NaN)
    variability = variability[variability["cycle_count"] > 1].fillna(0)
    
    return variability
import os
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "Ai models", "data", "processed", "forecasting_features_weekly.csv")

def build_features_for_next_week() -> pd.DataFrame:
    """
    Loads the pre-calculated features from the CSV (Option B).
    In a fully dynamic setup (Option A), this would query the SQLite DB 
    and manually calculate rolling means, holiday flags, lags, etc.
    For this demo, we extract the latest available week's features 
    from the perfectly engineered notebook data to pass into LightGBM.
    """
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Feature CSV not found at {CSV_PATH}")
    
    df = pd.read_csv(CSV_PATH)
    
    # The CSV should have 'item_name' and 'week_start' or similar.
    # We will just group by item_name and take the last row (chronologically).
    if 'week_start' in df.columns:
        df['week_start'] = pd.to_datetime(df['week_start'])
        df = df.sort_values('week_start')
        
    # Get the latest row for each item
    latest_df = df.groupby('item_name').tail(1).copy()
    
    # We also return the item_name so the service layer knows which prediction belongs to which item
    return latest_df

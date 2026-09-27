import pandas as pd
import os
from datetime import timedelta

# Cache for true news events
_NEWS_CACHE = None

def get_news_events():
    """
    Reads the exact dates and times of high impact news from the user-provided CSV.
    """
    global _NEWS_CACHE
    if _NEWS_CACHE is not None:
        return _NEWS_CACHE

    csv_path = 'XAUUSD_News_FOMC_NFP_CPI_PPI_PMI_2Y.csv'
    if not os.path.exists(csv_path):
        return pd.Series([])

    # Load news data
    df = pd.read_csv(csv_path, encoding='utf-16')
    
    # Filter for high impact news
    high_impact = df[df['Importance'] == 'CALENDAR_IMPORTANCE_HIGH'].copy()
    
    if high_impact.empty:
        _NEWS_CACHE = pd.Series([])
        return _NEWS_CACHE

    # Combine Date and Time into a single datetime string
    datetime_str = high_impact['Date'].astype(str).str.replace('.', '-') + ' ' + high_impact['Time'].astype(str)
    
    # Parse to datetime
    high_impact['datetime'] = pd.to_datetime(datetime_str)
    
    # Assume the times in the CSV are in UTC (or matched to the broker data)
    spikes = pd.Series(high_impact['datetime'].values).dt.tz_localize('UTC').sort_values()
    
    _NEWS_CACHE = spikes
    return _NEWS_CACHE


def is_news_embargo(current_time: pd.Timestamp, buffer_minutes: int = 15) -> bool:
    """
    Returns True if current_time is within `buffer_minutes` before or after a high-impact news event.
    """
    if not isinstance(current_time, pd.Timestamp):
        current_time = pd.to_datetime(current_time)
        
    if current_time.tzinfo is None:
        current_time = current_time.tz_localize('UTC')
            
    events = get_news_events()
    
    if events.empty:
        return False
    
    # Check if any event is within the window
    diffs = abs(events - current_time)
    min_diff = diffs.min()
    
    return min_diff <= timedelta(minutes=buffer_minutes)

def is_weekend_embargo(current_time: pd.Timestamp) -> bool:
    """
    Returns True if it's the weekend (Friday 21:45 UTC through Sunday 22:00 UTC).
    """
    if not isinstance(current_time, pd.Timestamp):
        current_time = pd.to_datetime(current_time)
        
    weekday = current_time.weekday()
    hour = current_time.hour
    minute = current_time.minute
    
    # Friday 21:45 onwards
    if weekday == 4:
        if hour > 21 or (hour == 21 and minute >= 45):
            return True
            
    # Saturday (all day)
    if weekday == 5:
        return True
        
    # Sunday before 22:00
    if weekday == 6:
        if hour < 22:
            return True
            
    return False

import sqlite3
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

try:
    conn = sqlite3.connect('C:/Users/vedan/.omniroute/storage.sqlite')
    
    tables_to_dump = [
        "provider_quota_state",
        "registered_keys",
        "provider_key_limits",
        "api_key_token_limits",
        "api_key_token_counters",
        "provider_connections"
    ]
    
    for table in tables_to_dump:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            print(f"\n--- {table.upper()} ---")
            if len(df) == 0:
                print("No data.")
            else:
                # for provider connections, select only interesting columns to save space
                if table == "provider_connections":
                    cols = [c for c in df.columns if 'id' in c or 'name' in c or 'provider' in c or 'status' in c or 'token' in c or 'limit' in c or 'used' in c]
                    print(df[cols].to_string())
                else:
                    print(df.to_string())
        except Exception as e:
            print(f"\n--- {table.upper()} ---")
            print("Error reading table:", e)

except Exception as e:
    print("Error:", e)

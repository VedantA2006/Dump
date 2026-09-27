import sys
sys.path.append(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137')
from security_guard import assert_no_dangerous_code

code = """
def calculate_signals(df):
    df['slope'] = df['close'].rolling(window=20).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
    return df
"""
try:
    assert_no_dangerous_code(code)
    print("Safe!")
except Exception as e:
    print("Caught:", str(e))

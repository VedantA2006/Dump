import re
from typing import Optional, Tuple

def _mutate_code_params(code: str, am: float, rr: float, lookback_param: Optional[Tuple[str, int]] = None) -> str:
    mutated = code
    if lookback_param:
        p_name, p_val = lookback_param
        mutated = re.sub(rf'\b({p_name})\s*=\s*\d+', rf'\g<1> = {p_val}', mutated)

    mutated = re.sub(r'\b([a-zA-Z0-9_]*atr[a-zA-Z0-9_]*)\s*=\s*[\d\.]+', rf'\g<1> = {am}', mutated)
    mutated = re.sub(r'\b([a-zA-Z0-9_]*rr[a-zA-Z0-9_]*|reward_risk_ratio|target_rr)\s*=\s*[\d\.]+', rf'\g<1> = {rr}', mutated)

    mutated = re.sub(
        r'([\+\-\(\*]\s*)[\d\.]+(\s*\*\s*[a-zA-Z0-9_]*atr[a-zA-Z0-9_]*\b)',
        rf'\g<1>{am}\g<2>',
        mutated
    )
    mutated = re.sub(
        r'([a-zA-Z0-9_]*atr[a-zA-Z0-9_]*\b\s*\*\s*)[\d\.]+',
        rf'\g<1>{am}',
        mutated
    )

    runner_rr = max(4.5, round(rr * 2.2, 1))
    risk_var_pattern = r'([a-zA-Z0-9_]*risk[a-zA-Z0-9_]*|[a-zA-Z0-9_]*sl_dist[a-zA-Z0-9_]*)'
    if 'tp2_long' in mutated or 'tp2_short' in mutated:
        mutated = re.sub(
            rf"(df\['tp1_long'\]\s*=\s*df\['close'\]\s*\+\s*\(?{risk_var_pattern}\s*\*\s*)[\d\.]+",
            rf"\g<1>{rr}",
            mutated
        )
        mutated = re.sub(
            rf"(df\['tp1_short'\]\s*=\s*df\['close'\]\s*-\s*\(?{risk_var_pattern}\s*\*\s*)[\d\.]+",
            rf"\g<1>{rr}",
            mutated
        )
        mutated = re.sub(
            rf"(df\['tp2_long'\]\s*=\s*df\['close'\]\s*\+\s*\(?{risk_var_pattern}\s*\*\s*)[\d\.]+",
            rf"\g<1>{runner_rr}",
            mutated
        )
        mutated = re.sub(
            rf"(df\['tp2_short'\]\s*=\s*df\['close'\]\s*-\s*\(?{risk_var_pattern}\s*\*\s*)[\d\.]+",
            rf"\g<1>{runner_rr}",
            mutated
        )
    else:
        mutated = re.sub(
            rf'\b{risk_var_pattern}\s*\*\s*[\d\.]+',
            rf'\g<1> * {rr}',
            mutated
        )
        mutated = re.sub(
            rf'[\d\.]+\s*\*\s*{risk_var_pattern}',
            rf'{rr} * \g<1>',
            mutated
        )
        if 'tp1_long' in mutated and 'tp2_long' not in mutated:
            mutated = re.sub(
                rf"(df\['tp1_long'\]\s*=\s*df\['close'\]\s*\+\s*\(?{risk_var_pattern}\s*\*\s*[\d\.]+\)?)",
                rf"\g<1>\n    df['tp2_long'] = df['close'] + (\g<2> * {runner_rr})\n    df['use_breakeven'] = True\n    df['use_trailing'] = True",
                mutated
            )
            mutated = re.sub(
                rf"(df\['tp1_short'\]\s*=\s*df\['close'\]\s*-\s*\(?{risk_var_pattern}\s*\*\s*[\d\.]+\)?)",
                rf"\g<1>\n    df['tp2_short'] = df['close'] - (\g<2> * {runner_rr})\n    df['use_breakeven'] = True\n    df['use_trailing'] = True",
                mutated
            )

    if 'use_trailing' not in mutated and 'use_breakeven' in mutated:
        mutated = mutated.replace("df['use_breakeven'] = True", "df['use_breakeven'] = True\n    df['use_trailing'] = True")

    return mutated

code = """
def calculate_signals(df):
    sw_highs, sw_lows = find_swings(df, swing_len = 5)
    bull_fvg_top, bull_fvg_bot, bear_fvg_top, bear_fvg_bot = find_fvgs(df)
    
    atr_val = atr(df, 20)
    sl_long = np.minimum(df['low'], sw_lows) - (1.2 * atr_val)
    sl_short = np.maximum(df['high'], sw_highs) + (1.2 * atr_val)

    risk_l = np.maximum(df['close'] - sl_long, 3.5)
    risk_s = np.maximum(sl_short - df['close'], 3.5)

    df['sl_long'] = df['close'] - risk_l
    df['sl_short'] = df['close'] + risk_s
    df['use_breakeven'] = True
    df['use_trailing'] = True
    df['tp1_long'] = df['close'] + (risk_l * 2.0)
    df['tp2_long'] = df['close'] + (risk_l * 4.5)
    df['tp1_short'] = df['close'] - (risk_s * 2.0)
    df['tp2_short'] = df['close'] - (risk_s * 4.5)
    return df
"""

print(_mutate_code_params(code, 2.0, 3.0))

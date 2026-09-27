import json
import pandas as pd
import matplotlib.pyplot as plt
from strategy_executor import execute_strategy

def main():
    # 1. Load strategy code from leaderboard
    data = json.load(open('data/leaderboard.json', encoding='utf-8'))
    strat = [s for s in data if s.get('name', '') == 'Tick and Volume Confluence (Round #117)'][0]
    
    # 2. Run Backtest on the Full Dataset
    df = pd.read_csv('data/XAUUSD_5m.csv', parse_dates=True)
    if 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'])
        df.set_index('datetime', inplace=True)
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    elif 'dt' in df.columns:
        df['datetime'] = pd.to_datetime(df['dt'])
        df.set_index('datetime', inplace=True)
        
    print("Data loaded, running backtest...")
    res = execute_strategy(strat['code'], df)
    
    stats = res.get('stats', {})
    trades_list = res.get('trades', [])
    trades = pd.DataFrame(trades_list)
    
    # 3. Generate HTML with Full Backtest Stats
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strategy Report (Full Backtest): {strat['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .chart {{ max-width: 800px; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <h1>Strategy Report (Full Backtest): {strat['name']}</h1>
        <p><strong>Author:</strong> {strat.get('author')}</p>
        
        <h2>Full Backtest Performance Statistics</h2>
        <table style="width:50%;">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Trades</td><td>{stats.get('total_trades', 0)}</td></tr>
            <tr><td>Win Rate</td><td>{stats.get('win_rate', 0):.2f}%</td></tr>
            <tr><td>Profit Factor</td><td>{stats.get('profit_factor', 0):.2f}</td></tr>
            <tr><td>Total PnL</td><td>${stats.get('total_pnl', 0):.2f}</td></tr>
            <tr><td>Net Profit %</td><td>{stats.get('net_profit_pct', 0):.2f}%</td></tr>
            <tr><td>Max Drawdown (%)</td><td>{stats.get('max_drawdown_pct', 0):.2f}%</td></tr>
            <tr><td>Max Drawdown ($)</td><td>${stats.get('max_drawdown', 0):.2f}</td></tr>
            <tr><td>Sharpe Ratio</td><td>{stats.get('sharpe_ratio', 0):.2f}</td></tr>
            <tr><td>Average PnL per Trade</td><td>${stats.get('avg_pnl', 0):.2f}</td></tr>
        </table>
        
        <h2>Equity and Drawdown Curves</h2>
"""
    
    if not trades.empty and 'entry_time' in trades.columns:
        trades['entry_time'] = pd.to_datetime(trades['entry_time'])
        trades = trades.sort_values('entry_time')
        trades['cumulative_pct'] = trades['pnl_percent'].cumsum()
        trades['drawdown_pct'] = trades['cumulative_pct'].cummax() - trades['cumulative_pct']
        
        # Calculate Monthly Returns
        trades['month_year'] = trades['entry_time'].dt.to_period('M')
        monthly_returns = trades.groupby('month_year')['pnl_percent'].sum()
        
        html_content += """
        <h2>Monthly Returns</h2>
        <table style="width:50%;">
            <tr><th>Month</th><th>Return (%)</th></tr>
"""
        for month, ret in monthly_returns.items():
            html_content += f"            <tr><td>{month.strftime('%b %Y')}</td><td>{ret:.2f}%</td></tr>\n"
            
        html_content += "        </table>\n"
        html_content += "        <h2>Equity and Drawdown Curves</h2>\n"
        
        import io
        import base64
        
        # Plot Equity Curve
        plt.figure(figsize=(10, 5))
        plt.plot(trades['entry_time'], trades['cumulative_pct'], label='Cumulative Return (%)', color='blue')
        plt.title('Equity Curve (%)')
        plt.xlabel('Date')
        plt.ylabel('Return (%)')
        plt.grid(True)
        plt.legend()
        buf_equity = io.BytesIO()
        plt.savefig(buf_equity, format='png')
        buf_equity.seek(0)
        img_str_equity = base64.b64encode(buf_equity.read()).decode('utf-8')
        plt.close()
        
        # Plot Drawdown Curve
        plt.figure(figsize=(10, 5))
        plt.fill_between(trades['entry_time'], -trades['drawdown_pct'], 0, color='red', alpha=0.3)
        plt.title('Drawdown Curve (%)')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True)
        buf_dd = io.BytesIO()
        plt.savefig(buf_dd, format='png')
        buf_dd.seek(0)
        img_str_dd = base64.b64encode(buf_dd.read()).decode('utf-8')
        plt.close()
        
        html_content += f"""
        <img class="chart" src="data:image/png;base64,{img_str_equity}" alt="Equity Curve">
        <br>
        <img class="chart" src="data:image/png;base64,{img_str_dd}" alt="Drawdown Curve">

        
        <h2>Trades Taken</h2>
        <table>
            <tr>
                <th>Trade ID</th>
                <th>Entry Time</th>
                <th>Exit Time</th>
                <th>Direction</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>PnL ($)</th>
                <th>PnL (%)</th>
                <th>Exit Reason</th>
            </tr>
"""
        for _, trade in trades.iterrows():
            html_content += f"""
            <tr>
                <td>{trade.get('id', '')}</td>
                <td>{trade.get('entry_time')}</td>
                <td>{trade.get('exit_time')}</td>
                <td>{trade.get('direction', '')}</td>
                <td>{trade.get('entry_price', 0):.2f}</td>
                <td>{trade.get('exit_price', 0):.2f}</td>
                <td>${trade.get('pnl', 0):.2f}</td>
                <td>{trade.get('pnl_percent', 0):.2f}%</td>
                <td>{trade.get('exit_reason', '')}</td>
            </tr>
"""
        html_content += """
        </table>
"""
    else:
        html_content += "<p>Could not generate curves/trades: No trades generated during backtest reproduction.</p>"
        
    html_content += """
    </body>
    </html>
"""
    with open('strategy_117_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("Report generated: strategy_117_report.html")

if __name__ == '__main__':
    main()

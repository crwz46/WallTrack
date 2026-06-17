import math
from datetime import datetime
from typing import Dict, List, Optional


class ChartGenerator:
    @staticmethod
    def ascii_bar_chart(
        data: List[Dict],
        label_key: str = "symbol",
        value_key: str = "total_value",
        title: str = "Token Distribution",
        width: int = 40,
    ) -> str:
        if not data:
            return "[No data]"

        max_val = max(d[value_key] for d in data)
        lines = [f"\n  {title}:\n"]

        for item in data:
            label = item[label_key][:10]
            val = item[value_key]
            bar_len = int((val / max_val) * width) if max_val > 0 else 0
            bar = "█" * bar_len
            lines.append(f"  {label:10s} | {bar} {val:>10.2f}")

        return "\n".join(lines)

    @staticmethod
    def ascii_timeline(
        tx_count: int,
        last_tx_time: Optional[str],
        title: str = "Activity",
    ) -> str:
        lines = [f"\n  {title}:\n"]
        bars = min(tx_count, 50)
        activity = "█" * (bars // 5) + "▓" * (bars % 5)
        lines.append(f"  Total Tx: {tx_count:,}")
        lines.append(f"  Activity: {activity}")
        if last_tx_time:
            lines.append(f"  Last Tx : {last_tx_time}")
        return "\n".join(lines)

    @staticmethod
    def to_html(data: Dict, filepath: str = None) -> str:
        lt = data.get("last_transaction") or {}
        tokens = data.get("top_tokens", [])

        token_rows = ""
        for t in tokens:
            token_rows += f"""
            <tr>
                <td>{t['symbol']}</td>
                <td>{t['contract'][:10]}...</td>
                <td>{t['total_value']:,.2f}</td>
                <td>{t['tx_count']}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WallTrack - {data['address'][:10]}...</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
            background: #0d1117; color: #c9d1d9; padding: 40px;
        }}
        .card {{
            background: #161b22; border: 1px solid #30363d;
            border-radius: 12px; padding: 24px; margin-bottom: 20px;
            max-width: 800px; margin-left: auto; margin-right: auto;
        }}
        h1 {{ color: #58a6ff; font-size: 24px; margin-bottom: 16px; }}
        h2 {{ color: #8b949e; font-size: 16px; text-transform: uppercase;
               letter-spacing: 1px; margin-bottom: 12px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .stat {{ background: #21262d; padding: 16px; border-radius: 8px; }}
        .stat .label {{ color: #8b949e; font-size: 12px; }}
        .stat .value {{ color: #f0f6fc; font-size: 20px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; color: #8b949e; font-size: 12px;
               padding: 8px; border-bottom: 1px solid #30363d; }}
        td {{ padding: 8px; border-bottom: 1px solid #21262d; }}
        .badge {{
            display: inline-block; background: #1f6feb; color: #fff;
            padding: 2px 8px; border-radius: 12px; font-size: 12px;
        }}
        .footer {{ text-align: center; color: #484f58; font-size: 12px;
                   margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🔍 WallTrack Report</h1>
        <div class="grid">
            <div class="stat">
                <div class="label">Address</div>
                <div class="value" style="font-size:14px">{data['address']}</div>
            </div>
            <div class="stat">
                <div class="label">Chain</div>
                <div class="value">{data['chain']} <span class="badge">{data['symbol']}</span></div>
            </div>
            <div class="stat">
                <div class="label">Balance</div>
                <div class="value">{data['native_balance']:.6f} {data['symbol']}</div>
            </div>
            <div class="stat">
                <div class="label">Transactions</div>
                <div class="value">{data['transaction_count']:,}</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Last Transaction</h2>
        <table>
            <tr><th>Hash</th><td>{lt.get('hash', 'N/A')[:20]}...</td></tr>
            <tr><th>From</th><td>{lt.get('from', 'N/A')}</td></tr>
            <tr><th>To</th><td>{lt.get('to', 'N/A')}</td></tr>
            <tr><th>Value</th><td>{lt.get('value', 'N/A')} ETH</td></tr>
            <tr><th>Time</th><td>{lt.get('timestamp', 'N/A')}</td></tr>
        </table>
    </div>

    <div class="card">
        <h2>Top Tokens</h2>
        <table>
            <tr><th>Symbol</th><th>Contract</th><th>Volume</th><th>TX</th></tr>
            {token_rows}
        </table>
    </div>

    <div class="footer">
        Generated by WallTrack on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""

        if filepath:
            with open(filepath, "w") as f:
                f.write(html)
        return html

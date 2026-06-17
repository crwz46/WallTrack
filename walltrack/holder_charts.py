import os
from typing import Dict, Optional


def generate_charts(
    report: Dict,
    output_dir: str = "charts",
) -> Dict[str, str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return {}

    os.makedirs(output_dir, exist_ok=True)
    symbol = report["token"]["symbol"]
    paths = {}

    # ===== Chart 1: Pie Chart - Top 10 vs Others =====
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    top10 = report["top_holders"]
    others_pct = 100 - sum(h["percentage"] for h in top10)

    labels = [f"{h['address'][:6]}...{h['address'][-4:]}" for h in top10] + ["Others"]
    sizes = [h["percentage"] for h in top10] + [max(0, others_pct)]
    colors = [
        "#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff",
        "#ff8fab", "#845ef7", "#36d399", "#f59e0b",
        "#ef4444", "#8b5cf6", "#374151",
    ]

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[: len(sizes)],
        textprops={"color": "#c9d1d9", "fontsize": 9},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_color("#c9d1d9")
        at.set_fontsize(8)

    ax.legend(
        wedges,
        labels,
        title="Top 10 Holders",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=8,
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="#c9d1d9",
    )

    ax.set_title(
        f"{symbol} Holder Distribution",
        color="#58a6ff",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    pie_path = os.path.join(output_dir, f"{symbol}_holder_pie.png")
    plt.tight_layout()
    plt.savefig(pie_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    paths["pie"] = pie_path

    # ===== Chart 2: Bar Chart - Top 20 Holders =====
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    top20 = report["holders"][:20]
    addresses = [
        f"{h['address'][:4]}..{h['address'][-4:]}"
        for h in top20
    ]
    percentages = [h["percentage"] for h in top20]

    bars = ax.barh(
        range(len(addresses)),
        percentages,
        color="#58a6ff",
        edgecolor="#1f6feb",
        height=0.7,
    )

    ax.set_yticks(range(len(addresses)))
    ax.set_yticklabels(addresses, fontsize=8, color="#c9d1d9")
    ax.invert_yaxis()

    ax.set_xlabel("Holding %", color="#8b949e", fontsize=10)
    ax.set_title(
        f"{symbol} - Top 20 Holders",
        color="#58a6ff",
        fontsize=14,
        fontweight="bold",
    )

    ax.spines["bottom"].set_color("#30363d")
    ax.spines["left"].set_color("#30363d")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#8b949e")
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#21262d", linewidth=0.5)

    for bar, pct in zip(bars, percentages):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{pct:.2f}%",
            va="center",
            fontsize=8,
            color="#c9d1d9",
        )

    bar_path = os.path.join(output_dir, f"{symbol}_holder_bar.png")
    plt.tight_layout()
    plt.savefig(bar_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    paths["bar"] = bar_path

    # ===== Chart 3: Gini Lorenz Curve =====
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    balances = sorted(
        [h["balance"] for h in report["holders"]]
    )
    n = len(balances)
    if n > 0:
        cum_share = [0]
        total = sum(balances)
        cum = 0
        for b in balances:
            cum += b
            cum_share.append(cum / total)

        pop_pct = [i / n for i in range(n + 1)]

        ax.plot(
            pop_pct, cum_share,
            color="#6bcb77", linewidth=2.5, label="Actual",
        )
        ax.plot(
            [0, 1], [0, 1],
            color="#ff6b6b", linewidth=1.5,
            linestyle="--", label="Equality",
        )

        gini = report["metrics"]["gini"]
        ax.fill_between(
            pop_pct, pop_pct, cum_share,
            alpha=0.1, color="#6bcb77",
            label=f"Gini = {gini:.4f}",
        )

    ax.set_xlabel("Population %", color="#8b949e", fontsize=10)
    ax.set_ylabel("Cumulative Holdings %", color="#8b949e", fontsize=10)
    ax.set_title("Lorenz Curve", color="#58a6ff", fontsize=14, fontweight="bold")

    ax.legend(
        fontsize=10,
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="#c9d1d9",
    )
    ax.spines["bottom"].set_color("#30363d")
    ax.spines["left"].set_color("#30363d")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#8b949e")
    ax.grid(color="#21262d", linewidth=0.5, alpha=0.5)

    lorenz_path = os.path.join(output_dir, f"{symbol}_lorenz_curve.png")
    plt.tight_layout()
    plt.savefig(lorenz_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    plt.close()
    paths["lorenz"] = lorenz_path

    print(f"\n  📊 Charts saved:")
    for k, v in paths.items():
        print(f"    {k:8s}: {v}")

    # Generate HTML report with embedded charts
    html_path = os.path.join(output_dir, f"{symbol}_report.html")
    _generate_html_report(report, paths, html_path)

    return paths


def _generate_html_report(
    report: Dict,
    chart_paths: Dict[str, str],
    output_path: str,
):
    t = report["token"]
    m = report["metrics"]

    # Convert chart paths to relative for HTML
    pie_rel = os.path.relpath(
        chart_paths.get("pie", ""), os.path.dirname(output_path)
    )
    bar_rel = os.path.relpath(
        chart_paths.get("bar", ""), os.path.dirname(output_path)
    )
    lorenz_rel = os.path.relpath(
        chart_paths.get("lorenz", ""), os.path.dirname(output_path)
    )

    top10_rows = ""
    for h in report["top_holders"]:
        top10_rows += f"""
        <tr>
            <td>{h['rank']}</td>
            <td style="font-family:monospace">{h['address'][:10]}...</td>
            <td>{h['percentage']:.2f}%</td>
            <td>{h['label'] or '—'}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{t['symbol']} - Holder Analysis | WallTrack</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
            background: #0d1117; color: #c9d1d9; padding: 30px;
        }}
        .card {{
            background: #161b22; border: 1px solid #30363d;
            border-radius: 12px; padding: 24px; margin: 0 auto 20px;
            max-width: 1000px;
        }}
        h1 {{ color: #58a6ff; font-size: 28px; }}
        h2 {{ color: #8b949e; font-size: 14px; text-transform: uppercase;
               letter-spacing: 1px; margin: 16px 0 8px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .stat {{
            background: #21262d; padding: 16px; border-radius: 8px;
            text-align: center;
        }}
        .stat .label {{ color: #8b949e; font-size: 11px; }}
        .stat .value {{ color: #f0f6fc; font-size: 22px; font-weight: bold; }}
        .danger {{ color: #ff6b6b !important; }}
        .warning {{ color: #ffd93d !important; }}
        .safe {{ color: #6bcb77 !important; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th {{ text-align: left; color: #8b949e; font-size: 11px;
               padding: 8px; border-bottom: 1px solid #30363d; }}
        td {{ padding: 8px; border-bottom: 1px solid #21262d; }}
        .chart-grid {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
            margin-top: 16px;
        }}
        .chart-grid img {{ width: 100%; border-radius: 8px;
                           border: 1px solid #30363d; }}
        .full-width {{ grid-column: 1 / -1; }}
        .footer {{
            text-align: center; color: #484f58; font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{m['risk_icon']} {t['symbol']} — Holder Analysis</h1>
        <p style="color:#8b949e;margin-top:4px">{t['name']}</p>

        <h2>Overview</h2>
        <div class="grid">
            <div class="stat">
                <div class="label">Total Supply</div>
                <div class="value">{t['total_supply']:,}</div>
            </div>
            <div class="stat">
                <div class="label">Top 10 Concentration</div>
                <div class="value {'danger' if m['top10_pct']>60 else 'warning' if m['top10_pct']>40 else 'safe'}">{m['top10_pct']:.1f}%</div>
            </div>
            <div class="stat">
                <div class="label">Gini Coefficient</div>
                <div class="value {'danger' if m['gini']>0.8 else 'warning' if m['gini']>0.6 else 'safe'}">{m['gini']:.4f}</div>
            </div>
            <div class="stat">
                <div class="label">Risk Level</div>
                <div class="value {m['risk_label']}">{m['risk_label']}</div>
            </div>
        </div>

        <h2>Top 10 Holders</h2>
        <table>
            <tr><th>#</th><th>Address</th><th>%</th><th>Label</th></tr>
            {top10_rows}
        </table>
    </div>

    <div class="card">
        <h2>Charts</h2>
        <div class="chart-grid">
            <img src="{pie_rel}" alt="Pie Chart">
            <img src="{bar_rel}" alt="Bar Chart">
            <img src="{lorenz_rel}" alt="Lorenz Curve" class="full-width"
                 style="max-width:600px;margin:0 auto;display:block">
        </div>
    </div>

    <div class="footer">
        Generated by WallTrack — Token Holder Analyzer
    </div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"    html    : {output_path}")

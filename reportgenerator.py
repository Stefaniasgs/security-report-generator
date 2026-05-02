import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

# --- 1. GERAÇÃO DE DADOS ---
random.seed(21)
np.random.seed(21)

INCIDENTS = 300
base = datetime(2025, 4, 1)
event_types = ["Brute Force", "SQL Injection", "Port Scan", "Malware", "Unauthorized Access", "Data Exfiltration"]
severities = ["Low", "Medium", "High", "Critical"]
sev_weights = [0.25, 0.35, 0.25, 0.15]
status_list = ["Resolved", "In Progress", "Open"]
status_weights = [0.55, 0.25, 0.20]
analysts = ["Ana Lima", "Carlos Melo", "Juliana Reis", "Stefania Guedes", "Rafael Costa"]
systems = ["Web Server", "Database", "Workstation", "Firewall", "VPN Gateway", "Mail Server"]
sev_num_map = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

records = []
for i in range(1, INCIDENTS + 1):
    sev = random.choices(severities, weights=sev_weights)[0]
    status = random.choices(status_list, weights=status_weights)[0]
    ts = base + timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))
    ttd = round(np.random.exponential(scale=30), 1)
    ttr = round(np.random.exponential(scale=120), 1) if status == "Resolved" else None
    records.append({
        "id": f"INC-{i:04d}", "timestamp": ts, "event_type": random.choice(event_types),
        "severity": sev, "sev_num": sev_num_map[sev], "affected_system": random.choice(systems),
        "analyst": random.choice(analysts), "status": status, "ttd_min": ttd, "ttr_min": ttr,
    })

df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)
df["date"] = df["timestamp"].dt.date

# --- 2. CÁLCULO DE KPIs ---
total = len(df)
critical_ct = int((df["severity"] == "Critical").sum())
open_ct = int((df["status"] == "Open").sum())
resolved_ct = int((df["status"] == "Resolved").sum())
in_progress = int((df["status"] == "In Progress").sum())
resolve_rate = round(resolved_ct / total * 100, 1)
avg_ttd = round(df["ttd_min"].mean(), 1)
avg_ttr = round(df["ttr_min"].mean(skipna=True), 1)
report_period = f"{df['date'].min()} a {df['date'].max()}"
generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- 3. COMPONENTES HTML ---
def status_badge(st):
    colors = {"Resolved": "#39d353", "In Progress": "#d29922", "Open": "#f85149"}
    color = colors.get(st, "#aaa")
    return f'<span style="background:{color}20;color:{color};padding:2px 8px;border-radius:4px;font-size:0.78rem;font-weight:600;border:1px solid {color}40;">{st}</span>'

daily = df.groupby("date").size().reset_index(name="count")
daily_max = daily["count"].max()
trend_bars_html = "".join([f'<div class="trend-col"><div class="trend-bar" style="height:{int(r["count"]/daily_max*100)}%;"></div></div>' for _, r in daily.iterrows()])

sev_colors = {"Critical": "#ff4040", "High": "#f97316", "Medium": "#d29922", "Low": "#58a6ff"}
sev_counts = df["severity"].value_counts().reindex(["Critical","High","Medium","Low"]).fillna(0)
sev_rows_html = "".join([f'<div class="sev-row"><span class="sev-dot" style="background:{sev_colors[s]};"></span><span>{s}</span><div class="sev-bar-wrap"><div class="sev-bar-fill" style="width:{round(c/total*100,1)}%;background:{sev_colors[s]};"></div></div></div>' for s, c in sev_counts.items()])

critical_df = df[df["severity"] == "Critical"].sort_values("timestamp", ascending=False).head(10)
critical_rows_html = "".join([f"<tr><td><code>{r['id']}</code></td><td>{r['event_type']}</td><td>{status_badge(r['status'])}</td></tr>" for _, r in critical_df.iterrows()])

# --- 4. TEMPLATE HTML ---
HTML_CONTENT = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  :root {{
    --bg: #0d1117; --panel: #161b22; --border: #21262d; --green: #39d353;
    --red: #f85149; --blue: #58a6ff; --text: #e6edf3; --muted: #8b949e;
  }}
  body {{ background: var(--bg); color: var(--text); font-family: sans-serif; padding: 20px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }}
  .card {{ background: var(--panel); border: 1px solid var(--border); padding: 15px; border-radius: 8px; }}
  .trend-wrap {{ display: flex; align-items: flex-end; height: 60px; gap: 2px; }}
  .trend-bar {{ background: var(--blue); flex: 1; min-width: 5px; }}
  .sev-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }}
  .sev-bar-wrap {{ flex: 1; background: #333; height: 8px; border-radius: 4px; }}
  .sev-bar-fill {{ height: 100%; border-radius: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid var(--border); }}
</style>
</head>
<body>
  <h2>Security Report</h2>
  <p style="color:var(--muted)">Period: {report_period}</p>
  
  <div class="kpi-grid">
    <div class="card">Total: {total}</div>
    <div class="card" style="color:var(--red)">Critical: {critical_ct}</div>
    <div class="card" style="color:var(--green)">Rate: {resolve_rate}%</div>
  </div>

  <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px;">
    <div class="card"><h3>Trend</h3><div class="trend-wrap">{trend_bars_html}</div></div>
    <div class="card"><h3>Severity</h3>{sev_rows_html}</div>
  </div>

  <div class="card" style="margin-top:20px;">
    <h3>Recent Criticals</h3>
    <table>{critical_rows_html}</table>
  </div>
</body>
</html>"""

# --- 5. SALVAR ---
with open("relatorio.html", "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

print("Sucesso! O arquivo 'relatorio.html' foi gerado.")
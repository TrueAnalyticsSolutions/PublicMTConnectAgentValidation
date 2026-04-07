#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path

status_dir = Path("status")
out_dir = Path("site")
badges_dir = out_dir / "badges"
out_dir.mkdir(parents=True, exist_ok=True)
badges_dir.mkdir(parents=True, exist_ok=True)

rows = []
for p in sorted(status_dir.glob("*.json")):
    rows.append(json.loads(p.read_text()))

rows.sort(key=lambda x: x.get("name", ""))
now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def resolve_status(row):
    status = row.get("status", "unknown")
    http_status = row.get("http_status") or row.get("status_code") or row.get("http_code")
    details = str(row.get("details") or "")

    if status == "error" or str(http_status) == "500" or "HTTP 500" in details or "status code 500" in details:
        return "error"
    return status

summary = {
    "generated_at": now,
    "total": len(rows),
    "compliant": sum(1 for r in rows if resolve_status(r) == "compliant"),
    "non_compliant": sum(1 for r in rows if resolve_status(r) == "non-compliant"),
    "unreachable": sum(1 for r in rows if resolve_status(r) == "unreachable"),
    "error": sum(1 for r in rows if resolve_status(r) == "error"),
    "agents": rows,
}
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

color_map = {"compliant": "brightgreen", "non-compliant": "orange", "unreachable": "red", "error": "crimson", "unknown": "lightgrey"}
for r in rows:
    status = resolve_status(r)
    badge = {
        "schemaVersion": 1,
        "label": r.get("name", "agent"),
        "message": status,
        "color": color_map.get(status, "lightgrey"),
    }
    (badges_dir / f"{r['slug']}.json").write_text(json.dumps(badge, indent=2))

status_meta = {
    "compliant": {"icon": "✅", "label": "Compliant", "class": "status-compliant"},
    "non-compliant": {"icon": "⚠️", "label": "Non-compliant", "class": "status-non-compliant"},
    "unreachable": {"icon": "❌", "label": "Unreachable", "class": "status-unreachable"},
    "error": {"icon": "🛑", "label": "Error", "class": "status-error"},
    "unknown": {"icon": "❔", "label": "Unknown", "class": "status-unknown"},
}

trs = []
for r in rows:
    probe_url = r.get("probe_url", "")
    link = f'<a href="{probe_url}">{probe_url}</a>' if probe_url else ""
    details = (r.get("details") or "").replace("<", "&lt;").replace(">", "&gt;")
    status = resolve_status(r)
    meta = status_meta.get(status, status_meta["unknown"])
    status_chip = f'<span class="status-chip {meta["class"]}">{meta["icon"]} {meta["label"]}</span>'
    trs.append(
        f"<tr><td>{r.get('name')}</td><td>{r.get('vendor','')}</td><td>{status_chip}</td><td>{details}</td><td>{link}</td></tr>"
    )

html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MTConnect Public Agent Compliance Report</title>
  <style>
    :root {{
      --bg: #f7f9fc;
      --surface: #ffffff;
      --border: #d8e1eb;
      --text: #12263a;
      --muted: #4f6478;
      --compliant-bg: #e7f8ef;
      --compliant-text: #0a6b3f;
      --non-compliant-bg: #fff4df;
      --non-compliant-text: #7a4c00;
      --unreachable-bg: #ffebeb;
      --unreachable-text: #8e1f1f;
      --error-bg: #ffeaf1;
      --error-text: #8a1246;
      --unknown-bg: #eef2f6;
      --unknown-text: #3a4b5c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      margin: 0;
      color: var(--text);
      background: linear-gradient(180deg, #f0f5fb 0%, var(--bg) 240px);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem 1.25rem 3rem;
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 2rem;
    }}
    .meta {{ color: var(--muted); margin: 0.25rem 0 0; }}
    .summary-grid {{
      margin: 1.5rem 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 0.75rem;
    }}
    .summary-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.9rem 1rem;
      box-shadow: 0 2px 8px rgba(18, 38, 58, 0.06);
    }}
    .summary-label {{ font-size: 0.82rem; color: var(--muted); }}
    .summary-value {{ margin-top: 0.25rem; font-size: 1.5rem; font-weight: 700; }}
    .status-chip {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      border-radius: 999px;
      padding: 0.28rem 0.55rem;
      font-size: 0.86rem;
      font-weight: 600;
      white-space: nowrap;
      border: 1px solid transparent;
    }}
    .status-compliant {{ background: var(--compliant-bg); color: var(--compliant-text); border-color: #b7e8cf; }}
    .status-non-compliant {{ background: var(--non-compliant-bg); color: var(--non-compliant-text); border-color: #ffe0a6; }}
    .status-unreachable {{ background: var(--unreachable-bg); color: var(--unreachable-text); border-color: #ffc6c6; }}
    .status-error {{ background: var(--error-bg); color: var(--error-text); border-color: #ffc7dc; }}
    .status-unknown {{ background: var(--unknown-bg); color: var(--unknown-text); border-color: #d6dee7; }}
    .table-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(18, 38, 58, 0.06);
    }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e8edf3; padding: 0.75rem 0.9rem; text-align: left; vertical-align: top; }}
    tr:last-child td {{ border-bottom: 0; }}
    th {{
      background: #f4f8fc;
      font-size: 0.84rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: var(--muted);
    }}
    a {{ color: #005fcc; }}
    a:hover {{ text-decoration: none; }}
  </style>
</head>
<body>
  <main>
    <h1>MTConnect Public Agent Compliance Report</h1>
    <p class=\"meta\">Generated at {now} UTC</p>
    <div class=\"summary-grid\">
      <div class=\"summary-card\"><div class=\"summary-label\">📊 Total Agents</div><div class=\"summary-value\">{summary['total']}</div></div>
      <div class=\"summary-card\"><div class=\"summary-label\">✅ Compliant</div><div class=\"summary-value\">{summary['compliant']}</div></div>
      <div class=\"summary-card\"><div class=\"summary-label\">⚠️ Non-compliant</div><div class=\"summary-value\">{summary['non_compliant']}</div></div>
      <div class=\"summary-card\"><div class=\"summary-label\">❌ Unreachable</div><div class=\"summary-value\">{summary['unreachable']}</div></div>
      <div class=\"summary-card\"><div class=\"summary-label\">🛑 Error</div><div class=\"summary-value\">{summary['error']}</div></div>
    </div>
    <div class=\"table-wrap\">
      <table>
        <thead><tr><th>Agent</th><th>Vendor</th><th>Status</th><th>Details</th><th>Probe URL</th></tr></thead>
        <tbody>
          {''.join(trs)}
        </tbody>
      </table>
    </div>
  </main>
</body>
</html>
"""
(out_dir / "index.html").write_text(html)

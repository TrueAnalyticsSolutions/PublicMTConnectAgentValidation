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

summary = {
    "generated_at": now,
    "total": len(rows),
    "compliant": sum(1 for r in rows if r.get("status") == "compliant"),
    "non_compliant": sum(1 for r in rows if r.get("status") == "non-compliant"),
    "unreachable": sum(1 for r in rows if r.get("status") == "unreachable"),
    "agents": rows,
}
(out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

color_map = {"compliant": "brightgreen", "non-compliant": "orange", "unreachable": "red", "unknown": "lightgrey"}
for r in rows:
    status = r.get("status", "unknown")
    badge = {
        "schemaVersion": 1,
        "label": r.get("name", "agent"),
        "message": status,
        "color": color_map.get(status, "lightgrey"),
    }
    (badges_dir / f"{r['slug']}.json").write_text(json.dumps(badge, indent=2))

trs = []
for r in rows:
    probe_url = r.get("probe_url", "")
    link = f'<a href="{probe_url}">{probe_url}</a>' if probe_url else ""
    details = (r.get("details") or "").replace("<", "&lt;").replace(">", "&gt;")
    trs.append(
        f"<tr><td>{r.get('name')}</td><td>{r.get('vendor','')}</td><td>{r.get('status')}</td><td>{details}</td><td>{link}</td></tr>"
    )

html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MTConnect Public Agent Compliance Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .meta {{ color: #555; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <h1>MTConnect Public Agent Compliance Report</h1>
  <p class=\"meta\">Generated at {now} UTC</p>
  <p class=\"meta\">Total: {summary['total']} | Compliant: {summary['compliant']} | Non-compliant: {summary['non_compliant']} | Unreachable: {summary['unreachable']}</p>
  <table>
    <thead><tr><th>Agent</th><th>Vendor</th><th>Status</th><th>Details</th><th>Probe URL</th></tr></thead>
    <tbody>
      {''.join(trs)}
    </tbody>
  </table>
</body>
</html>
"""
(out_dir / "index.html").write_text(html)

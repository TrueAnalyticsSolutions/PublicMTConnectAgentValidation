#!/usr/bin/env python3
import datetime as dt
import html
import json
import re
import uuid
from pathlib import Path

VALIDATOR_BASE_URL = "https://validator.tams.ai"
REPORT_UTM_QUERY = "utm_source=github&utm_medium=badge&utm_campaign=mtconnect_validation"

def resolve_status(row):
    status = row.get("status", "unknown")
    http_status = row.get("http_status") or row.get("status_code") or row.get("http_code")
    details = str(row.get("details") or "")

    if status == "error" or str(http_status) == "500" or "HTTP 500" in details or "status code 500" in details:
        return "error"
    return status


def safe_slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return value or "agent"


def normalize_report_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError):
        return None


def report_markup(row, status):
    report_id = normalize_report_id(row.get("report_id"))
    if not report_id or status not in {"compliant", "non-compliant"}:
        return '<span class="report-unavailable">Validation report unavailable</span>'

    name = html.escape(str(row.get("name") or "agent"), quote=True)
    report_url = f"{VALIDATOR_BASE_URL}/{report_id}?{REPORT_UTM_QUERY}"
    escaped_report_url = html.escape(report_url, quote=True)
    badge_url = f"{VALIDATOR_BASE_URL}/badges/reports/{report_id}.svg"
    embed_url = f"{VALIDATOR_BASE_URL}/embed/reports/{report_id}"
    return f"""
      <div class="report-cell">
        <a href="{escaped_report_url}" target="_blank" rel="noopener noreferrer">
          <img src="{badge_url}" alt="MTConnect validation status for {name}" loading="lazy" />
        </a>
        <details class="report-details">
          <summary>View embedded report</summary>
          <iframe
            data-src="{embed_url}"
            title="Validation report for {name}"
            width="100%"
            height="220"
            loading="lazy"
            referrerpolicy="strict-origin-when-cross-origin"
            sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
          ></iframe>
          <noscript><a href="{escaped_report_url}">Open the full validation report</a></noscript>
        </details>
      </div>
    """


def generate_site(status_dir=Path("status"), out_dir=Path("site")):
    badges_dir = out_dir / "badges"
    out_dir.mkdir(parents=True, exist_ok=True)
    badges_dir.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(status_dir.glob("*.json"))]
    for row in rows:
        row["report_id"] = normalize_report_id(row.get("report_id"))
    rows.sort(key=lambda x: x.get("name", ""))
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    summary = {
        "generated_at": now,
        "total": len(rows),
        "compliant": sum(1 for r in rows if resolve_status(r) == "compliant"),
        "non_compliant": sum(1 for r in rows if resolve_status(r) == "non-compliant"),
        "unreachable": sum(1 for r in rows if resolve_status(r) == "unreachable"),
        "error": sum(1 for r in rows if resolve_status(r) == "error"),
        "agents": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    color_map = {"compliant": "brightgreen", "non-compliant": "orange", "unreachable": "red", "error": "crimson", "unknown": "lightgrey"}
    for r in rows:
        status = resolve_status(r)
        badge = {
            "schemaVersion": 1,
            "label": r.get("name", "agent"),
            "message": status,
            "color": color_map.get(status, "lightgrey"),
        }
        (badges_dir / f"{safe_slug(r.get('slug', 'agent'))}.json").write_text(json.dumps(badge, indent=2), encoding="utf-8")

    status_meta = {
        "compliant": {"icon": "✅", "label": "Compliant", "class": "status-compliant"},
        "non-compliant": {"icon": "⚠️", "label": "Non-compliant", "class": "status-non-compliant"},
        "unreachable": {"icon": "❌", "label": "Unreachable", "class": "status-unreachable"},
        "error": {"icon": "🛑", "label": "Error", "class": "status-error"},
        "unknown": {"icon": "❔", "label": "Unknown", "class": "status-unknown"},
    }

    trs = []
    for r in rows:
        probe_url = str(r.get("probe_url") or "")
        escaped_probe_url = html.escape(probe_url, quote=True)
        link = f'<a href="{escaped_probe_url}">{escaped_probe_url}</a>' if probe_url else ""
        name = html.escape(str(r.get("name") or ""), quote=True)
        vendor = html.escape(str(r.get("vendor") or ""), quote=True)
        details = html.escape(str(r.get("details") or ""), quote=True)
        slug = safe_slug(r.get("slug", name))
        status = resolve_status(r)
        meta = status_meta.get(status, status_meta["unknown"])
        status_chip = f'<span class="status-chip {meta["class"]}">{meta["icon"]} {meta["label"]}</span>'
        trs.append(
            f'<tr id="agent-{slug}"><td>{name}</td><td>{vendor}</td><td>{status_chip}</td>'
            f'<td>{details}</td><td>{link}</td><td>{report_markup(r, status)}</td></tr>'
        )

    page = f"""<!doctype html>
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
      overflow-x: auto;
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
    tr:target {{ outline: 3px solid #78aee8; outline-offset: -3px; }}
    .report-cell {{ min-width: 210px; }}
    .report-cell img {{ display: block; max-width: 100%; height: auto; }}
    .report-details {{ margin-top: 0.6rem; }}
    .report-details summary {{ color: #005fcc; cursor: pointer; font-weight: 600; }}
    .report-details iframe {{ display: block; width: min(640px, 80vw); max-width: 640px; border: 0; margin-top: 0.65rem; }}
    .report-unavailable {{ color: var(--muted); font-size: 0.88rem; }}
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
        <thead><tr><th>Agent</th><th>Vendor</th><th>Status</th><th>Details</th><th>Probe URL</th><th>Validation Report</th></tr></thead>
        <tbody>
          {''.join(trs)}
        </tbody>
      </table>
    </div>
  </main>
  <script>
    document.querySelectorAll(".report-details").forEach((details) => {{
      details.addEventListener("toggle", () => {{
        if (!details.open) return;
        const frame = details.querySelector("iframe[data-src]");
        if (!frame) return;
        frame.setAttribute("src", frame.dataset.src);
        frame.removeAttribute("data-src");
      }}, {{ once: true }});
    }});
  </script>
</body>
</html>
"""
    (out_dir / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    generate_site()

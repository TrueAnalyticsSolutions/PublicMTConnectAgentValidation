#!/usr/bin/env python3
import json
import re
from pathlib import Path


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "agent"


agents = json.loads(Path("public-agents.json").read_text())
items = []
seen = set()

for agent in agents.get("agents", []):
    name = agent["name"]
    host = agent["host"]
    base = slugify(name)
    slug = base
    n = 2
    while slug in seen:
        slug = f"{base}-{n}"
        n += 1
    seen.add(slug)
    items.append(
        {
            "name": name,
            "vendor": agent.get("vendor", ""),
            "host": host,
            "slug": slug,
        }
    )

print(json.dumps({"include": items}))

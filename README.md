# Public MTConnect Agent Validation

Automated validation for publicly available MTConnect Agent `/probe` responses.

## Agent compliance badges

| Agent | Badge |
|---|---|
| Stratasys F3300 | ![Stratasys F3300](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/stratasys-f3300.json) |
| Stratasys F450mc | ![Stratasys F450mc](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/stratasys-f450mc.json) |
| Stratasys F370CR | ![Stratasys F370CR](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/stratasys-f370cr.json) |
| Stratasys F900 | ![Stratasys F900](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/stratasys-f900.json) |
| MTConnect Institute Demo | ![MTConnect Institute Demo](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mtconnect-institute-demo.json) |
| Mazak MFMS10-MC1 | ![Mazak MFMS10-MC1](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-mfms10-mc1.json) |
| Mazak MFMS10-MC2 | ![Mazak MFMS10-MC2](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-mfms10-mc2.json) |
| Mazak Mill w/SMooth-G | ![Mazak Mill w/SMooth-G](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-mill-w-smooth-g.json) |
| Mazak MFMS18-MC1 HCN Q | ![Mazak MFMS18-MC1 HCN Q](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-mfms18-mc1-hcn-q.json) |
| Mazak M12345 | ![Mazak M12345](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-m12345.json) |
| Mazak M12346 3 axis mill | ![Mazak M12346 3 axis mill](https://img.shields.io/endpoint?url=https://trueanalyticssolutions.github.io/PublicMTConnectAgentValidation/badges/mazak-m12346-3-axis-mill.json) |

## What this repository does

- Reads each public agent endpoint from `public-agents.json`.
- On a schedule (weekly) or manual trigger, fetches each remote `GET /probe` response.
- Validates each probe response using `TrueAnalyticsSolutions/mtconnect-validator-action@v4`.
- Publishes a live status report and per-agent badge JSON to the `gh-pages` branch.

## Workflows

- **Reusable workflow**: `.github/workflows/validate-agent.yml`
  - Validates one agent (`name`, `vendor`, `host`, `slug`) and uploads a status artifact.
- **Scheduled orchestrator**: `.github/workflows/weekly-public-agent-validation.yml`
  - Runs every Monday at 08:00 UTC (`0 8 * * 1`), fans out over all agents in `public-agents.json`, aggregates results, and publishes GitHub Pages content.

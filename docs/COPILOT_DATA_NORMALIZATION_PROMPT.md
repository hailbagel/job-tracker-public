# Copilot Prompt — Normalize Provider Data and Repair HyImpulse

Copy the prompt below into **GitHub Copilot Chat in VS Code** while the repository root is open.

---

## Prompt

You are working inside the repository `hailbagel/job-tracker-public`.

Your task is to **normalize provider outputs around the repository's existing canonical schema and repair the current HyImpulse data-quality problem**.

### Important: understand the existing architecture first

Before changing any code:

1. Inspect:
   - `jobtracker/processing.py`
   - `jobtracker/acquisition.py`
   - `jobtracker/pipeline.py`
   - `configs/sources.json`
   - `scripts/publish_public_data.py`
   - the provider implementations under `scrapers/providers/`
   - representative files under `data/*/processed/`
   - the existing tests

2. Treat the schema already defined in `jobtracker/processing.py` as the current canonical normalized schema.

The important existing definitions are:

```python
LATEST_FIELDS = (
    "id",
    "source_id",
    "source_job_id",
    "title",
    "location",
    "company",
    "department",
    "link",
    "scrape_timestamp",
)

DETAIL_FIELDS = LATEST_FIELDS + (
    "mission",
    "requirements",
    "benefits",
)
```

**Do not create a second competing schema module such as `schemas/job_schema.py` unless you can prove the existing canonical schema cannot serve the requirement. Prefer one source of truth.**

### Problem 1 — inconsistent processed CSVs

The repository contains legacy processed datasets whose columns are not identical across providers.

Audit at least:

- `data/spacex/processed/`
- `data/neura/processed/`
- `data/jacobs/processed/`
- `data/tesla/processed/`
- `data/hyimpulse/processed/`
- `data/exolaunch/processed/`
- `data/rocket-factory-augsburg/processed/`

For each standard output:

- `jobs_latest.csv`
- `job_details.csv`
- `job_history.csv`
- `job_changes.csv`
- `department_summary.csv`
- `location_summary.csv`

determine whether the file matches the schema produced by the current shared processing layer.

The goal is that **new successful acquisitions produce consistent normalized files regardless of provider**.

Do not blindly rewrite historical data. If tracked legacy files need a one-time migration, make that explicit, deterministic, testable, and minimal.

### Problem 2 — HyImpulse currently reports success with bad data

Current HyImpulse data is structurally valid but semantically poor.

Observed examples include:

```text
title = APPLY NOW
location = Unknown
department = Unknown
mission = ""
requirements = ""
benefits = ""
```

The current registry entry uses `html_job_links`.

Investigate the actual HyImpulse / Personio public source and repair acquisition so that it captures the real job information.

Prefer a structured public Personio source/API/XML feed when available over scraping generic "Apply now" links.

For HyImpulse, a successful acquisition should provide, where exposed by the official public source:

- stable source job id
- real title
- location
- company
- department
- canonical job URL
- meaningful job description / mission
- requirements
- benefits when available

Do not fabricate unavailable values. Empty optional fields are acceptable; fake values are not.

### Design requirements

Keep the implementation simple.

- Reuse `jobtracker.processing.process_success()` wherever appropriate.
- Reuse existing acquisition adapters where possible.
- Add a reusable adapter only when it clearly reduces provider-specific code.
- Preserve `configs/sources.json` as the source registry.
- Preserve last-known-good data behavior on failed/incomplete acquisition.
- Preserve truthful `data/source_status.json` semantics.
- Preserve the Patrick feed behavior.
- Do not weaken publication validation.
- Do not modify Hostinger systemd files, scheduler cadence, SSH, credentials, or deployment configuration.
- Do not modify the 24-hour problem-source watcher unless required by a directly related documentation reference.
- Do not add `data/all_jobs.csv` as a new source of truth. If a consolidated dataset is useful, treat it only as a derived output and explain why before adding it.

### Tests

Add or update tests that prove:

1. normalized successful sources emit the canonical schemas;
2. extra provider-specific input fields do not leak into normalized CSVs unless intentionally part of the canonical model;
3. missing optional values normalize safely;
4. HyImpulse no longer emits `APPLY NOW` as every title;
5. HyImpulse produces real locations/departments when the official source exposes them;
6. failed or incomplete sources do not overwrite last-known-good normalized datasets;
7. existing SpaceX, NEURA, RFA, Exolaunch and Patrick-feed behavior remains intact.

Use fixtures/mocks for provider tests where possible. Do not depend on live internet access for the normal unit test suite.

### Workflow

Work directly in this VS Code workspace.

1. Inspect and explain the current mismatch first.
2. Give me a concise implementation plan before editing.
3. Then make the smallest coherent set of code/test changes.
4. Run the relevant tests.
5. Run `git diff --check`.
6. Show me:
   - files changed
   - tests run and results
   - remaining known limitations
   - whether any tracked data migration is required

Do **not** commit, push, merge, create a PR, alter production, or modify credentials. Stop after local code changes and verification so I can review the diff first.

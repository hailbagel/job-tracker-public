# Copilot task — Exolaunch missing detail descriptions (post-production data audit)

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


## Ground truth — 13 October 2026

Read-only full data audit completed on Hostinger at `/opt/vutrulabs/job-tracker-public`:

```text
[CHECK] neura: current=204 detail=204 history=349 changes=910
[WARN] tesla: failed collection; 8117 preserved entries are STALE
[WARN] jacobs: failed collection; 130 preserved entries are STALE
[CHECK] spacex: current=2741 detail=2741 history=3023 changes=3284
[CHECK] rocket-factory-augsburg: current=52 detail=52 history=62 changes=0
[CHECK] exolaunch: current=11 detail=11 history=11 changes=2
[WARN] exolaunch: 9/11 details lack all description fields
[CHECK] hyimpulse: current=22 detail=22 history=22 changes=22
[WARN] NEURA auxiliary jobs_structured.csv=181 vs current=204; review purpose
[CHECK] patrick feed: 2826 JSON and CSV records
[CHECK] spacex feed: 2741 JSON and CSV records
[CHECK] tracked data files: 54
=== AUDIT COMPLETE: 0 failures / 4 warnings ===
```

There are **no detected structural errors** under the implemented checks. This is **not proof of complete upstream vacancy coverage**. Exolaunch is a data-quality limitation, not an excuse to overwrite or fabricate data.

## Objective (single blocker)

Diagnose why 9 out of 11 Exolaunch jobs have empty `mission`, `requirements`, and `benefits` even though their IDs, titles, and canonical rows are valid. Distinguish between:

1. Public Personio XML source does not publish descriptions for these positions.
2. `jobtracker/acquisition.py::personio_xml()` misses a legitimate XML variant.
3. The official linked public job detail pages expose text that the current generic adapter does not collect.

## Do first (read-only investigation)

Review `configs/sources.json`, `jobtracker/acquisition.py`, `jobtracker/processing.py`, `jobtracker/patrick.py`, `tests/test_personio_xml.py`, and representative published Exolaunch output.

Investigate the official `https://exolaunch.jobs.personio.com/xml` endpoint and only authorized public official job-detail pages. If upstream cannot be reached, identify precisely which check failed and stop without inventing a fix.

Known examples with no description in current published dataset:

- `exolaunch:2504264` — Test Engineer - Mechanical Space Systems (m/w/d)
- `exolaunch:2782697` — Mechanical Design Engineer - EXOtube (CAD Specialist)
- `exolaunch:2799954` — International Logistics Specialist (m/w/d)

Nine total blank-description rows exist; confirm the full current set rather than hardcoding a list.

## Implementation constraints

- Fix the **smallest reusable acquisition layer** only when evidence supports the change. Preserve the shared Personio adapter's HyImpulse behavior.
- Do not fill empty fields with invented job text, placeholders, or content from unrelated roles.
- Keep source collection status separate from *detail completeness*. Do not silently call fully described jobs `complete` when description data is unavailable. Any change in completeness semantics must preserve the publisher's current fail-closed rules and have regression coverage.
- Preserve existing CSV/JSON schemas, canonical IDs/URLs, job history, changes, and approved Patrick ranking unless a schema change is separately authorized.
- Preserve all other existing sources, including the verified HyImpulse Personio feed.
- Do not change Hostinger, systemd, timer, secrets, credentials, private profile, or production `data/` files as part of this investigation.

## Tests and acceptance

Add a fixture-based regression test reproducing the diagnosed missing-detail case. Run all relevant Personio, registry, publication and Patrick tests plus `git diff --check`. Report:

- Root cause, with observable evidence and exact upstream behavior.
- Count of Exolaunch jobs with complete / missing descriptions.
- Which fields and adapter pathways are affected.
- Whether fully populated descriptions are obtainable lawfully and reliably.
- Whether the issue is **fixed**, **source-limited**, or **still blocked**.
- Files changed, test results, and residual risks.

**Stop after reviewable code/tests and push a feature branch and PR; no merge or production deployment without separate approval.** Never force-push or weaken protections.

## Follow-on priorities (not in scope of this task)

- Clarify NEURA `jobs_structured.csv` (181 auxiliary rows) vs 204 canonical jobs before deleting or reclassifying anything.
- Tesla HTTP 403 and Jacobs collector failure: treat retained 8117/130 jobs as stale, and investigate legitimate public data sources without bypassing access controls.
- Update `ROADMAP.md` to reflect observed Hostinger production acceptance (with evidence) after owner review; currently its delivery statuses are stale.
- Verify the next unattended scheduled publication; only afterward consider regularizing the read-only audit in the operational quality gate.

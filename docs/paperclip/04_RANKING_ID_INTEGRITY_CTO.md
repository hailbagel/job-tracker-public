# PAPERCLIP TASK – Ranking-IDs gegen Quell-IDs abgleichen

**STATUS:** NACH F1/F2, CTO. **Ziel:** Paperclip → VuTruLabs → New Task. Jeden der folgenden vier Codeblöcke **einzeln** in das zugehörige Feld kopieren. **Nicht** in VS Copilot. Noch kein Paperclip-Task durch diese Repo-Datei angelegt.

## Title
```text
JT-RANKING-ID-INTEGRITY – Reconcile ranked IDs against active sources
```

## Assignee
```text
CTO
```

## Project
```text
Job Tracker Public
```

## Prompt
```text
Role: CTO engineering agent, VuTruLabs Paperclip.
Task: JT-RANKING-ID-INTEGRITY – finish existing GitHub Issue #24 independently.
Repo: https://github.com/hailbagel/job-tracker-public
Issue: https://github.com/hailbagel/job-tracker-public/issues/24

Verified gap: scripts/audit_public_data.py check_feed() validates JSON/CSV count and order, scanned metadata and markdown counts but not the exact published ranking-ID set against each eligible current jobs_latest.csv ID. The same number of jobs may hide ID turnover. No actual wrong ID set has yet been proven; do not invent examples.

1. Inspect current main/PRs and Issue #24. Use a distinct clean feature branch and do not collide with F1 or F2 work. Keep PRs isolated.
2. Define eligible current providers from the registry, appropriate feed/sector/tags, successful complete acquisition and current jobs_latest.csv; preserve exact source-qualified ID semantics and correct fail-closed behavior for incomplete/stale providers.
3. Implement exact ID-set equality for Patrick feed and SpaceX feed where appropriate, with informative missing/extra ID examples and source-level counts. Existing duplicate-ID, current/detail link, active/history and JSON/CSV ordering checks must remain.
4. Add deterministic negative tests for same-count turnover, stale rank snapshots with matching JSON/CSV, wrong provider, duplicate IDs, missing/extra provider and failed acquisitions; positive tests for eligible complete sources and normal no-change publish.
5. Read-only public data audit; never rewrite datasets, invoke collectors, alter scheduled production, expose profile data, modify source_status or adjust host cadence.
6. Tests + Ubuntu CI + git diff --check, one new DRAFT PR referencing Issue #24, no merge/deploy. Do not block F1 by working in its checkout.
7. Post exact PR SHA and CI evidence with actual expected-versus-published set comparison on existing tracked public data, and explain what remains unknown.

Done: same-count stale turnover cannot pass, exact feed-to-source current IDs verified, code/tests/docs and one draft PR.
```

---

Kein autonomes Mergen, Hostinger-Deployment oder Zugriff auf private Bewerberdaten. PR/Tests/Status im Paperclip-Task dokumentieren.

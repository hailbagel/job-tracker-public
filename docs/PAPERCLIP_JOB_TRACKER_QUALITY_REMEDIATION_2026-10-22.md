# Paperclip – Job Tracker Qualitätsreparatur (22. Oktober 2026)

**Quintessenz:** Priorität 1 ist Ranking-Vertrauen und 6-h-Monitoring. **Neue Quellen (Mesabi, Siemens, Midrex) zunächst zurückstellen**, solange fehlende Anforderungen zu falschen GREEN-Treffern führen. Keine laufenden Arbeitsbereiche eines anderen Agenten ändern. Ein bereits begonnener Mesabi-Draft-PR darf ohne Merge abgeschlossen werden, aber keine Produktivaktivierung.

**WO EINFÜGEN:** Paperclip → VuTruLabs → **New Task**. Pro Task **vier getrennte Copy-Boxen** einzeln kopieren: `Title`, `Assignee`, `Project`, `Prompt`. Projektname entspricht der UI: `Job Tracker Public`. Eine Datei in GitHub erstellt noch keinen Paperclip-Task.

**Reihenfolge / Ressourcen:** F1 zuerst beim CTO; F2 und F3 nacheinander auf separaten Branches (oder belegbar unabhängigen Worktrees), keine Doppelarbeit. Die unabhängige Top-10-Prüfung kann beim Chief of Staff parallel laufen. Maximal zwei gleichzeitig programmierende Agents am selben Repository, besser nur ein CTO-Writer. Produktions-Merge und Hostinger sind jeweils separate Freigaben.

**Bereits nachgewiesen:** RFA 55/55 `requirements` leer, Originalanzeigen zeigen Qualifikationen; sechs Stunden Scheduler vs. 60 Stunden Monitor. F3 ist eine belegte Prüflücke, kein Nachweis einer derzeit falschen veröffentlichten ID-Menge.

**Nicht verwenden:** VUT-318 wurde vom Owner als falsch zugeordnet markiert und wird ignoriert.

---

## P0 – RFA Pflichtanforderungen / GREEN-Schutz

**ZUERST:** Die fehlerhaften GREEN-Treffer sind bis zur Korrektur nicht als verifiziert zu verwenden. CTO-Entwicklung; kein Produktionsdeploy.

### Title
```text
JT-RFA-QUALIFICATIONS – Repair Greenhouse fields and hard gates
```

### Assignee
```text
CTO
```

### Project
```text
Job Tracker Public
```

### Prompt
```text
Role: CTO implementation agent, VuTruLabs Paperclip.
Task: JT-RFA-QUALIFICATIONS – correct the false-GREEN ranking pathway.
Repo: https://github.com/hailbagel/job-tracker-public
Issue: https://github.com/hailbagel/job-tracker-public/issues/27
Priority: P0. Do not delay this work for Mesabi or additional source adapters.

Ground truth verified 2026-10-22:
- jobtracker/acquisition.py greenhouse() sets mission=item["content"] without mapping requirements.
- Snapshot data/rocket-factory-augsburg/processed/job_details.csv contains 55 current rows, all 55 requirements blank, though mission HTML has qualifications sections.
- jobtracker/patrick.py accepts any of mission/requirements/benefits as sufficient, and analysis/profile_ranking.py uses requirements for mandatory hard gates.
- Snapshot data/patrick/processed/patrick_targets.md (2026-10-21) shows RFA 4997134101 GREEN 77, 4944174101 GREEN 73, both with "Hard gates: none".
- Public originals: https://job-boards.eu.greenhouse.io/rocketfactoryaugsburgag/jobs/4997134101 and https://job-boards.eu.greenhouse.io/rocketfactoryaugsburgag/jobs/4944174101

Implementation:
1. Inspect current origin/main, all open PRs, relevant source, existing parsers/tests and the exact Issue #27. Confirm no competing PR. Work in isolated clean workspace/feature branch feature/rfa-qualifications-gate. If checkout dirty, do not reset/stash/delete or overwrite work. Stop as BLOCKED if needed.
2. Parse Greenhouse job HTML into canonical mission / requirements / benefits structurally, including headings "Your Qualifications", "Must-Have Skills", "Requirements", "Your Tasks", preferred/optional qualification subsections. Use HTML parser/normalization and synthetic fixtures; do not hallucinate job requirements. Original content can remain available as source provenance without contaminating normalized fields.
3. Guard ranking against unknown/incomplete required qualifications: missing/ambiguous/unparseable must never become verified GREEN merely because zero hard gates were detected. Record UNKNOWN or equivalent explicit unverified status; do not mark a mismatch RED without candidate evidence. Preserve useful score as indicative but not verified suitability. Ensure behavior also works for sources whose normalized requirements already exist (especially SpaceX).
4. Tests MUST include public job IDs 4997134101 and 4944174101 with required years/domain/degree text in synthetic public fixtures; assert no falsely verified GREEN for unknown/unsupported mandatory criteria, no false eligibility from keywords alone. Include positive proof for genuinely satisfied requirements, optional vs mandatory, empty HTML, malformed headings, no stated requirements, rerun idempotence and last-good preservation.
5. Do not access, copy or commit private candidate profiles, access tokens, actual personal applications or production data. Use synthetic candidate eligibility fixtures. Do not modify Hostinger/systemd, publisher timing, current datasets, or unrelated Mesabi adapter.
6. Run focused and full relevant tests, lint/compile and git diff --check. Commit code/tests/docs on isolated branch; push once and open ONE DRAFT PR referencing Issue #27. CI Ubuntu evidence required; fix real failures on same branch. Never merge or deploy without separate approval.
7. Post here: PR URL, commit SHA, tests/CI results, before/after false-GREEN demonstration for the two IDs, qualification parser coverage and unresolved risk. If tests or permission fail, mark BLOCKED, not DONE.

Definition of done: Auditable non-green guard for missing mandatory qualifications, reproducible tests including both RFA examples, green CI, one draft PR, no production changes.
```

---

## P1 – Scheduler-Frischemonitor korrigieren

**NACH F1 / separater Branch:** Monitoring-Code und Tests reparieren, keine Hostinger-Änderung ohne Freigabe.

### Title
```text
JT-SCHEDULER-MONITOR – Align alerts with six-hour schedule
```

### Assignee
```text
CTO
```

### Project
```text
Job Tracker Public
```

### Prompt
```text
Role: CTO engineering agent, VuTruLabs Paperclip.
Task: JT-SCHEDULER-MONITOR – correct six-hour scheduler freshness monitoring.
Repo: https://github.com/hailbagel/job-tracker-public
Issue: https://github.com/hailbagel/job-tracker-public/issues/28

Evidence: scripts/hostinger_scheduler_state.py MINIMUM_INTERVAL=RETRY_INTERVAL=6h; scripts/check_hostinger_scheduler.py uses STALE_AFTER=60h and returns success while last_success is under 60h. This hides missed six-hour cycles. Do NOT redesign or silently change the production six-hour scheduler.

1. Start only after CTO has finished/paused F1, or in a separately isolated safe worktree. Inspect current main and PRs. No duplicate branch, reset, stash or forced pushes.
2. Make the read-only health check genuinely cadence-aware using durable state, expected eligibility deadline, last attempt status, effective timer/service state and explicitly justified configurable grace. Distinguish successful skipped hourly checks, six-hour eligibility, in-progress, first-run bootstrap, cooldown after failure, missed success, timer disabled, malformed/future timestamps and clock drift.
3. Return actionable WARN and nonzero CRITICAL/FAIL for overdue runs or actual failures, including when last success age is below 60h. Do not treat skipped eligibility checks or unchanged output data as failed production runs.
4. Add deterministic mocked-timestamp and systemd-property tests for normal six-hour operation, several missed cycles, failed last attempt after prior success, last_success future, missing state, reboot/persistent state and disabled timer; verify actual exit codes.
5. Keep checker read-only, secrets private, no SSH/write actions, no production publish and no systemd restart, enable, daemon-reload, schedule or cadence change.
6. Produce new isolated feature branch and ONE draft PR referencing Issue #28; focused tests, full applicable suite, Ubuntu CI, git diff --check. No merge/deploy.
7. Post PR/commit links, evidence for chosen grace/thresholds and host-only verification command for later operator review (read-only); cite conditions that require a separate deploy/rollback decision.

Done: code+tests+draft PR, monitoring can detect missed six-hour production cycles, no production changes.
```

---

## P1 – Ranking-IDs gegen tatsächliche Stellen abgleichen

**SEPARATE AUFGABE:** Das bestehende GitHub Issue #24 nutzen. Keine neue Issue-Dublette.

### Title
```text
JT-RANKING-ID-INTEGRITY – Reconcile ranked IDs against active sources
```

### Assignee
```text
CTO
```

### Project
```text
Job Tracker Public
```

### Prompt
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

## P1 – Unabhängige Prüfung der zehn Top-Treffer

**READ-ONLY, parallel möglich:** Nur öffentlich sichtbare Stelleninformationen und die veröffentlichten Ranking-Begründungen untersuchen. Falsch zugeordnetes VUT-318 ausdrücklich nicht weiterverwenden.

### Title
```text
JT-TOP10-QA – Verify ranking evidence against official job postings
```

### Assignee
```text
Chief of Staff
```

### Project
```text
Job Tracker Public
```

### Prompt
```text
Role: Independent reviewer / Chief of Staff, VuTruLabs Paperclip.
Task: JT-TOP10-QA – independent public evidence QA for ranking trust.
Repo: https://github.com/hailbagel/job-tracker-public
Reference defect: https://github.com/hailbagel/job-tracker-public/issues/27
Do not reuse or claim findings from misassigned Paperclip task VUT-318.

1. Read the tracked 2026-10-21 public ranking snapshot top_25 (first ten entries). Record the exact snapshot timestamp and rank/job ID from that public file, not from live scraped market assumptions.
2. For each of exactly ten listings, fetch its official PUBLIC original job posting via a permitted browser/web tool, if still online. Record date/access, status and whether text is available. Do not bypass anti-bot protection, logins, challenges, or robots. If changed/removed mark UNVERIFIABLE and preserve snapshot evidence.
3. Compare public ranking explanations with original job requirements. Identify degree, mandatory experience, authorization/ITAR, hard domain requirements, licenses, work location and optional/preferred criteria. Do not guess the user's private qualifications or declare eligibility without verified data; this is an evidence-quality review, not a personal background scan.
4. Flag evidence failures: mandatory qualification omitted, unknown or empty requirements, status GREEN despite missing verification, ranking points that do not establish hard eligibility, URL/ID mismatch and old snapshot. Distinguish verified defects from source changes and unknowns.
5. Deliver a ten-row QA table with job ID, employer/title, original URL, extracted mandatory requirements, ranking-status/known gates, discrepancy severity, checked-at and evidence. Provide findings count only for this sample; do not generalize accuracy to all jobs. Call out the two known RFA IDs explicitly and quantify how many of the TEN were checkable.
6. Do not edit code, create duplicate implementation tasks, commit profile data, open PR, merge, apply for jobs, or activate Hostinger. Provide suggested acceptance criteria for CTO's Issue #27 PR. Avoid real candidate PII.
7. Post a compact PASS/RISK/BLOCKED summary with all ten evidence links and uncertainties into THIS task; stop.

Done: independent public ten-job audit, transparent unknowns, no changes to production.
```

---

## Abnahme-Gate für Wartungsmodus

Keine pauschale Abnahme vor (1) RFA Hard-Gate-Regression mit 2 Originalbeispielen, (2) zehn manuell geprüften Top-Treffern, (3) exact ranked-ID/source-ID invariant, (4) wirksamer Warn-/Error-Status für verpasste 6-h-Läufe, (5) drei tatsächlich erfolgreiche, voneinander unabhängige **geplante** 6-h-Produktionsläufe anhand Hostinger-Journal und durablem Status auch nach zulässigem Neustart, (6) dokumentierten Stale-Sourcen und (7) eindeutig installierter Host-Version. Ein gleicher Daten-Commit ist kein Scheduler-Ausfall; GitHub CI ist kein Host-Deploymentnachweis.

**Erst danach:** Mesabi CTO-Draft-PR aus [Paperclip Mesabi Auftrag](PAPERCLIP_MESABI_AGENT_IMPLEMENTATION.md) erneut priorisieren. Alle Coding-Agents müssen auf ihren isolierten Git-Branches arbeiten; sie dürfen nie selbst Produktionsdaten, geheime Profile oder Hostinger verändern. [Verbindliches Paperclip-Schema](PAPERCLIP_TASK_FORMAT.md).

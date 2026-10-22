# Paperclip – Historische Job-Tracker-Tasks (21.10.2026)

**Status:** VUT-317, VUT-319 und VUT-320 waren in Paperclip bereits als **Done** sichtbar. VUT-318 ist laut Owner falsch zugeordnet und wird **ignoriert**. Diese Datei ist eine **historische, neu formatierte Task-Ablage, keine Aufforderung zur Neuerstellung**.

**Aktiver neuer Coding-Auftrag:** [Paperclip CTO – Mesabi JazzHR Adapter](PAPERCLIP_MESABI_AGENT_IMPLEMENTATION.md).

**Einheitliches Kopierformat:** [PAPERCLIP_TASK_FORMAT.md](PAPERCLIP_TASK_FORMAT.md). Wo ein Task neu angelegt werden soll: Paperclip → VuTruLabs → Tasks → New Task; jeden der vier Codebloecke einzeln kopieren. Kein Terminal/Copilot. Keine Aufgabe wird durch das Speichern im Repo in Paperclip erzeugt.

---

## VUT-317 – Health Check (bereits Done)

Im Screenshot vom 21.10.2026 als Done zu sehen. Nicht erneut anlegen.

### Title
```text
VUT-PAPERCLIP-HEALTH – Read-only agent heartbeat smoke test
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
Task: VUT-PAPERCLIP-HEALTH — validate VuTruLabs Paperclip task execution.

Objective: One controlled read-only heartbeat. Confirm this Paperclip instance, the assigned agent, and task update permissions work before any more agent task is run.

1. Read your own agent identity, assigned task and company/project metadata through normal Paperclip mechanisms.
2. Report whether the agent runtime starts, whether the assigned task can be read, and whether one concise status comment can be posted to this SAME task.
3. Check whether prior known environment blockers remain: API URL redirect HTTP→HTTPS and bubblewrap (bwrap) user-namespace restriction. Report only observed evidence, not assumptions.
4. Report task ID, agent name/ID, heartbeat/run outcome, and actual error if any. Never output secrets, auth headers or private content.
5. Do not spawn/delegate child tasks, install dependencies, change server configuration, create/edit repositories or touch Hostinger.
6. Mark the task blocked if the runtime/API permission is not working. Stop after one check. Do not claim success without an observed task comment and successful heartbeat record.

Definition of done: An observable heartbeat and a readable single status comment with PASS / BLOCKED / FAIL and evidence. No other changes.
```

---

## VUT-318 – Datenqualitaet (ignorieren)

Der Owner hat VUT-318 als falsch zugeordnet bezeichnet. **Nicht erneut anlegen oder als belastbares Ergebnis weiterverwenden.**

### Title
```text
JT-DATA-QUALITY – Independent ranking and source audit
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
Task: JT-DATA-QUALITY — independent READ-ONLY assessment for https://github.com/hailbagel/job-tracker-public/issues/24

Repository: https://github.com/hailbagel/job-tracker-public
Purpose: Review current data quality; do NOT duplicate the separate Copilot implementation work for Issue #24.

1. Inspect main branch documentation, scripts/audit_public_data.py, data contracts and current tracked public data only.
2. Identify which source-status checks are demonstrably guaranteed and which remain risk areas. Explicitly investigate same-count ID turnover: feed JSON and CSV can agree with each other and still be stale compared with current jobs_latest.csv.
3. Compare only publicly tracked aggregate records and published job IDs. Distinguish Tesla/Jacobs stale last-good data from fresh successful source collections. Do not access private Patrick profiles.
4. Check that SpaceX and Patrick ranking IDs should be validated independently against eligible current sources; SMS group Industrial data must not enter Space/Rocket rankings.
5. Create a concise risk matrix: severity, observed evidence, current validation coverage, recommended test and which component should own the fix.
6. Return links to relevant GitHub issues/docs and a suggested acceptance checklist for Copilot's future Draft PR. Do not change code, datasets, CI, Paperclip schedule or Hostinger.

Deliverable: Task comment, concise PASS/RISK/BLOCKED report and a 5-point regression acceptance checklist. No PR or deploy.
```

---

## VUT-319 – Industriequellen (bereits Done)

VUT-319 wurde abgeschlossen und lieferte Mesabi als bevorzugte erste Implementierung. Nicht erneut anlegen.

### Title
```text
JT-INDUSTRIAL-SOURCES – Midrex, Mesabi, Siemens source feasibility
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
Task: JT-INDUSTRIAL-SOURCES — public, read-only source feasibility review.

Repository context: https://github.com/hailbagel/job-tracker-public
Employers: Midrex Technologies, Mesabi Metallics, Siemens AG. Do not conflate Siemens AG with Siemens Energy. SMS group is covered by existing PR #25 and should not be onboarded again.

Research each employer's official public careers pages and any explicitly allowed, stable listing APIs/feeds. Report:
(a) official careers listing URL,
(b) ATS provider/platform if verifiable,
(c) permitted complete-listing source including pagination/count and job-detail URLs,
(d) descriptions, locations, timestamps and durable job identifiers available,
(e) robots/access constraints and known blockers,
(f) recommendation: viable / manual discovery / blocked, with evidence URLs.
Avoid robots.txt-disallowed paths, login pages, authentication bypasses, private APIs and scraping anti-bot controls.
No code modification, API keys, production imports, unpublished data writing or GitHub PRs.
Deliver a three-row comparison, uncertainty notes and one next recommended implementation candidate, with separate owner approval needed.
```

---

## VUT-320 – SMS Readiness (bereits Done)

VUT-320 war in Paperclip als Done markiert. Inhaltliche Abnahme bleibt getrennt; nicht erneut anlegen.

### Title
```text
JT-SMS-READINESS – independent rollout checklist
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
Task: JT-SMS-READINESS — independent READ-ONLY readiness review.

PR #25 is merged to job-tracker-public main, but that does NOT demonstrate live SMS collection on Hostinger. Inspect current repo code, opt-in gates, tracked bootstrap fixtures, tests, publisher data allowlist and source-status audit contracts plus docs/COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md.

Produce: exact pre-flight evidence list, rollback readiness, known data completeness limitations, scheduler invariant and conditions that would qualify a later controlled SMS pilot for PASS / FAIL. Identify missing Hostinger-only verification without trying to perform it.

NEVER set JOB_TRACKER_ENABLE_SMS_GROUP, do not touch SSH/systemd/Hostinger, trigger collectors, publish data, edit production files, merge PRs or change schedules. No default activation. Work solely with available read-only public repo evidence.

Deliverable: compact owner decision sheet with prerequisites, risks and source citations/paths. Flag all unverified live-host conditions as OPEN.
```

---

## Neue aktive Arbeit

Die naechste eigenstaendige Paperclip-Aufgabe fuer den CTO ist [JT-MESABI-JAZZHR](PAPERCLIP_MESABI_AGENT_IMPLEMENTATION.md); die vorherige VUT-319 war nur die Machbarkeitsrecherche. CTO darf Branch, synthetische Tests und einen Draft-PR erstellen, aber nichts auf Hostinger aktivieren oder mergen.

**Praezision:** Fuer historische Tasks sind die Assignee-/Project-Felder als wiederverwendbare Vorgaben aus der aktuellen Job-Tracker-Zuordnung geschrieben; sie bestaetigen nicht zwingend die urspruenglich in Paperclip gespeicherten alten Task-Metadaten. Den tatsächlichen alten Taskstatus ausschliesslich in Paperclip pruefen.

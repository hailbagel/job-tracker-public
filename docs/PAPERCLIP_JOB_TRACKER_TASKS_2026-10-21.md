# Paperclip – Job Tracker Arbeitsauftraege (21.10.2026)

**System:** VuTruLabs / Paperclip. **Scope:** `hailbagel/job-tracker-public`.  
**WO EINFUEGEN:** Paperclip Web UI → VuTruLabs → richtiges Projekt `Job Tracker` (falls vorhanden) → **New Task / New Issue** → je einen Titel und die darunterstehende Beschreibung kopieren → dem zustaendigen Agent zuweisen. Ein GitHub-Issue ist **kein** Paperclip-Task. Die Erstellung in Paperclip erfolgt separat.

**Grundsatz:** Maximal **3 Tasks gleichzeitig in Arbeit**. Nach jedem Task nur ein explizit angestossener Heartbeat. Keine automatischen Folgeauftraege, keine Subtasks, keine Agentenrekrutierung, keine Merge-/Publish-/Hostinger-Aktionen. Kein Zugriff auf private Profile, Zugangsdaten, lokale Chat-Backups. Alle Ausgaben als Task-Kommentar oder verlinkte, nicht-vertrauliche GitHub-Dokumentation. Ohne Owner-Freigabe keine Git-Mutationen. Die Aufgaben sind **Vorlagen** und wurden nicht auf Paperclip erstellt oder ausgefuehrt.

## P0 – Zuerst: Paperclip Agent Smoke Test

**Titel:** `VUT-PAPERCLIP-HEALTH – Read-only agent heartbeat smoke test`  
**Prioritaet:** Critical / P0  
**Assignee:** Chief of Staff (sofern konfiguriert); sonst ein bekannter funktionierender Agent.  
**Projekt:** VuTruLabs Operations / Platform.  
**Zeitfenster:** Einmaliger Test. Keine automatische Wiederholung.

**Beschreibung in Paperclip kopieren:**

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

**Gate:** Nur bei PASS mit den weiteren Tasks beginnen. Bei FAIL nicht im laufenden Job-Tracker/Hostinger-Deployment debuggen; Paperclip gesondert behandeln.

---

## P1 – Datenqualitaetsanalyse (GitHub Issue #24)

**Titel:** `JT-DATA-QUALITY – Independent ranking and source audit`  
**Prioritaet:** High / P1  
**Assignee:** Quality/Data Agent, falls vorhanden; sonst Chief of Staff.

**Beschreibung in Paperclip kopieren:**

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

**Nicht ueberlappen:** Copilot-Entwicklung zum [Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24) bleibt unabhaengig. Paperclip gibt nur Review-Evidenz.

---

## P1 – Industrie-Firmenanalyse

**Titel:** `JT-INDUSTRIAL-SOURCES – Midrex, Mesabi, Siemens source feasibility`  
**Prioritaet:** High / P1  
**Assignee:** Research/Market Intelligence Agent, falls vorhanden; sonst Chief of Staff.

**Beschreibung in Paperclip kopieren:**

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

**Erwartetes Ergebnis:** belastbare Machbarkeitsentscheidung, nicht sofort neue Scraper.

---

## P2 – SMS group Produktionsfreigabe (spaeter)

**Titel:** `JT-SMS-READINESS – independent rollout checklist`  
**Prioritaet:** Medium / P2  
**Assignee:** Engineering Operations / QA Agent, falls vorhanden.

**Beschreibung in Paperclip kopieren:**

```text
Task: JT-SMS-READINESS — independent READ-ONLY readiness review.

PR #25 is merged to job-tracker-public main, but that does NOT demonstrate live SMS collection on Hostinger. Inspect current repo code, opt-in gates, tracked bootstrap fixtures, tests, publisher data allowlist and source-status audit contracts plus docs/COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md.

Produce: exact pre-flight evidence list, rollback readiness, known data completeness limitations, scheduler invariant and conditions that would qualify a later controlled SMS pilot for PASS / FAIL. Identify missing Hostinger-only verification without trying to perform it.

NEVER set JOB_TRACKER_ENABLE_SMS_GROUP, do not touch SSH/systemd/Hostinger, trigger collectors, publish data, edit production files, merge PRs or change schedules. No default activation. Work solely with available read-only public repo evidence.

Deliverable: compact owner decision sheet with prerequisites, risks and source citations/paths. Flag all unverified live-host conditions as OPEN.
```

---

## Operativer Ablauf

1. **P0 starten** → einmal Heartbeat/Invoke manuell und PASS/FAIL dokumentieren. Wenn FAIL: Rest nicht starten.
2. **P1 Datenqualitaet** und **P1 Firmenanalyse** starten → separate Tasks, beide read-only, maximal drei Tasks inklusive Health Check.
3. **P2 SMS** erst nach Abschluss eines P1-Tasks bzw. freiem Agentenslot anlegen.
4. Paperclip darf Ergebnisse koordinieren; Copilot implementiert codebezogene Aenderungen auf separatem Git-Branch mit CI und Review. Produktionsaktionen bleiben bei einem separaten Owner-Review.

## Abhaengigkeiten und bekannte Unbekannte

- Das Paperclip-VPS hatte in frueheren Tests einen API-Redirect-/bwrap-Blocker. Der aktuelle Livezustand ist **nicht** durch GitHub nachgewiesen.
- Issue #24 ist nach aktuellem GitHub-Stand offen; PR #25 ist gemergt, SMS aber default-off.
- **Keine direkte Paperclip-Verbindung** ist in dieser ChatGPT-Sitzung verfuegbar: Diese Datei ist eine copy-ready Task-Sammlung, keine Bestaetigung, dass Paperclip-Aufgaben erstellt wurden.

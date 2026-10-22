# Kopieren 02 — GitHub Copilot Agent in VS Code

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Aufgaben stehen unter [Paperclip-Tasks: vier Kopierfelder je Agent](paperclip/README.md). Nicht doppelt ausführen; kein Hostinger-Deploy.


**WO EINFÜGEN?** Auf dem **Betriebslaptop**, in VS Code, nach erfolgreichem Schritt 01, rechts im **Chat / Copilot → Agent**. Dafür **einen neuen Copilot-Chat** anlegen mit dem Thema `Job Tracker — Industrial Sources`. Den Text unten vollständig in das Chat-Eingabefeld einfügen und absenden. **Nicht** in PowerShell, Hostinger oder eine Markdown-Datei einfügen.

**WOFÜR?** Startet die technische Analyse und Implementierung für SMS group, Midrex, Mesabi Metallics und Siemens AG, mit eigenem Feature-Branch, Tests und Draft-PR. Der Agent soll die vollständige, bereits versionierte Spezifikation lesen; dieser Startauftrag vermeidet doppelten langen Kontext im Chat.

## Diesen gesamten Block in Copilot Agent kopieren

```text
You are the engineering lead for hailbagel/job-tracker-public, running in a NEW VS Code Copilot Agent chat on the work laptop.

FIRST, before editing any file:
1. Confirm the open folder and clean Git branch main, aligned with origin/main. If the worktree is dirty or there is a divergent branch, STOP and report it. Do not reset, clean, stash, overwrite or force-push.
2. Read ALL of docs/COPILOT_INDUSTRIAL_WORK_LAPTOP_HANDOFF_2026-10-21.md and docs/COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md. Also read ENGINEERING_PRINCIPLES.md, PUBLIC_REPOSITORY_POLICY.md, configs/sources.json, jobtracker/registry.py, jobtracker/acquisition.py, jobtracker/pipeline.py, jobtracker/processing.py, scripts/publish_public_data.py, scripts/audit_public_data.py and relevant tests.
3. Treat GitHub origin/main as the single source of truth. The Hostinger publisher pushes data commits roughly every six hours; avoid conflicting with it. The latest confirmed successful production publication was 2026-10-21T04:05:02Z with 0 audit failures and two known stale-source warnings (Tesla, Jacobs). Do not infer later uptime or runs without evidence.

MISSION:
Automate industrial and plant-engineering job coverage, starting with SMS group, then Midrex Technologies, Mesabi Metallics and Siemens AG. The four source IDs already exist in configs/sources.json as manual_discovery: sms-group, midrex, mesabi-metallics, siemens. Do not create duplicate registry entries. Siemens Energy is NOT Siemens AG.

STEP A — RESEARCH / DECISION:
For all four sources, verify official careers pages and any actually accessible authorized listing/detail feeds. Record exact URL and platform, access restrictions, completeness and pagination evidence, canonical job IDs, detailed descriptions, locale, dates and deduplication strategy. Create a dated, four-source feasibility table in docs/. Never claim 200 OK proves a complete job listing. Respect 401/403/429, CAPTCHA and no-crawl restrictions. No access-control circumvention, no private sessions or credentials.

STEP B — CODING:
Choose SMS group first IF a reliable legally accessible source can actually be demonstrated (d.vinci is only a hypothesis until checked). Implement the smallest correct, testable adapter and source contract in the existing registry/acquisition architecture, with repeatable finite full pagination and fail-closed handling for incomplete or blocked requests. If SMS is blocked, document the blocker and proceed to the next verified public source instead. One source per PR. Provide native stable IDs, official detail links, fields and descriptions without fabricated values. Keep any new source manual in production until tracked output bootstrap, publisher allowlist, publisher integration, provenance and full data audit are reviewed separately.

STEP C — QUALITY GATES:
Add deterministic mocked/fixture tests for pagination, complete listing, ID stability, duplicate prevention, descriptions, zero results, malformed/partial feeds, 401/403/429, repeat collections, history integrity and preservation of previous good data. Preserve the repaired SpaceX history invariant and all existing Space/Rocket Patrick feed behavior; industrial jobs belong in a proposed separate industrial/construction ranking, not mixed silently into the Space/Rocket ranking. Run target tests, Python compile, git diff --check and the full test suite on Ubuntu GitHub Actions (Windows fcntl limitations are not a reason to hack production code). Report exact test results, limitations and CI links.

GIT WORKFLOW:
Create feature/industrial-sms-source or another source-specific feature branch ONLY AFTER confirming a clean synchronized local main. Stage only intended source/config/test/docs changes; no live data outputs, no tokens, no candidate files or private Patrick profile. Commit and git push -u origin <feature-branch>, then open a DRAFT PR to main. Do not merge, deploy to Hostinger, change any scheduler/service/timer, touch private settings, or trigger the live publisher. Do not write direct changes to main. No force pushes.

FINAL RESPONSE:
Briefly report a four-source feasibility matrix; chosen first adapter and completeness proof; source tests + Linux CI; commit SHA and PR URL; risks/limits; and exact owner approval required to continue. If a blocker occurs, give concrete evidence and do not invent success.

Start with STEP A. Do not request new inputs until you have inspected the files and official sources.
```

## Erwartetes Ergebnis

Ein Vier-Unternehmen-Feasibility-Bericht, ein erster testbarer Adapter **oder dokumentierter Blocker**, GitHub-Feature-Branch, erfolgreiche Linux-Checks und ein **Draft Pull Request**. **Kein Merge und keine Hostinger-Installation ohne erneute Freigabe.**

Referenzdokumente:
- [Work-laptop handoff, production baseline, full implementation rules](COPILOT_INDUSTRIAL_WORK_LAPTOP_HANDOFF_2026-10-21.md)
- [Original industrial source specification](COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md)

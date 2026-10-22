# PAPERCLIP TASK – Mesabi Metallics JazzHR Adapter

> **PRIORITÄTSÄNDERUNG 22.10.2026:** Dieser Mesabi-Adapterauftrag ist **vorläufig nachrangig**, weil [P0 RFA-GREEN-Falschtreffer und weitere Qualitätsmängel](PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md) zuerst behoben werden müssen. **Noch nicht gestarteten Mesabi-Task nicht starten.** Bei bereits aktiver Entwicklung keine Arbeit löschen; Branch isoliert halten und nur als Draft-PR vorlegen, nicht mergen/deployen.


**Verwendung:** Paperclip → VuTruLabs → Tasks → New Task. Jeden der **vier** `Plain text`-Bloecke mit dem GitHub-Kopiersymbol **einzeln** kopieren und in das entsprechende Paperclip-Feld einfuegen. **Nicht** als einen einzigen Prompt kopieren.

**Task-Typ:** Coding & Tests · **Prioritaet:** High · **Projektbezug:** [GitHub Issue #26](https://github.com/hailbagel/job-tracker-public/issues/26), Paperclip VUT-319 (Feasibility abgeschlossen). **Nicht** in VS Code/Copilot starten.

## Title
```text
JT-MESABI-JAZZHR – CTO agent implementation and CI
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
Task: JT-MESABI-JAZZHR – implement tested adapter via Paperclip agent (GitHub Issue #26)

Role: You are the CTO / engineering execution agent in VuTruLabs Paperclip. You are authorized to implement code, synthetic fixtures, tests and docs in a NEW feature branch and to push a DRAFT PR, subject to the preflight below. You are NOT authorized to merge, deploy, change production scheduler, or enable collection on Hostinger. No Copilot or VS Code interaction is required.

Repository: https://github.com/hailbagel/job-tracker-public
Existing issue: https://github.com/hailbagel/job-tracker-public/issues/26
Research evidence: Paperclip VUT-319 (done 2026-10-21)
Source: https://www.mesabimetallics.com/careers/ ; linked public JazzHR Mesabi Metallics Company LLC board https://essar.applytojob.com/
Separate industrial SMS adapter/PR #25 already exists; do not reimplement it. Ignore unrelated company mesabi.com.

EXECUTION CONTRACT
1. FIRST check your current runtime, workspace/repo checkout, allowed file paths, current branch/status, ability to run Python tests, and GitHub remote/write authentication. Check that paperclip task workspace is dedicated and that no other agent owns the same checkout/branch. If missing repo workspace or Git push permission: report BLOCKED with evidence rather than pretending to commit or using any private token workaround.
2. Read configs/sources.json; jobtracker/acquisition.py, pipeline.py, processing.py, registry.py; synthetic tests/fixtures, docs/INDUSTRIAL_EMPLOYER_FEASIBILITY_2026-10-21.md, and GitHub Issue #26. Confirm actual status of main and whether a Mesabi adapter already exists. If already in development in another branch or PR, STOP and report duplicate rather than creating a competing implementation.
3. Use a clean isolated branch named feature/mesabi-jazzhr-agent. Never force-push, reset, clean or stash unrelated work. If local checkout is dirty, use a safe new clone/worktree in an approved Paperclip workspace or mark BLOCKED; never delete pre-existing files.
4. Build an isolated read-only parser/adapter for public, robots-permitted listing and job-detail URLs. No login, application endpoints, /cb routes, CAPTCHA bypass, disallowed robots paths, private API or user-agent spoofing. Respect rate limits; no recurring live scraping during development.
5. Extract stable opaque JazzHR job IDs from /apply/<id>/... paths, canonical job URLs, title, company, location, substantive detail descriptions/job type only when supported. Do not invent publishing timestamps or locations. Follow the existing normalized _job(...) contract. Exclude applicant forms and tracking metadata.
6. Full-coverage validation is mandatory: enumerate current publicly published board IDs, account for complete listing/pagination where applicable, validate each ID against detail pages, and reject duplicate/ambiguous/unreachable IDs or incomplete details. Historical snapshots showed varying counts (45/46/47 across surfaces); these are observations, not a fixed threshold. Reconcile fresh simultaneous source evidence or label completeness unverified. Fail closed on incomplete snapshots; do NOT replace prior last-good data.
7. Keep mesabi-metallics in manual_discovery / non-production status. Do not add to production publishing allowlists, public feeds, Patrick/SpaceX ranking, source_status or any Hostinger/systemd routine. Existing SMS group opt-in also stays unchanged.
8. Write deterministic offline synthetic tests for empty/partial/duplicate list, same-count turnover, detail mismatch, missing description, malformed HTML/encoding, stable IDs, blocked/disallowed path, and preservation of last-good on failure. Run focused tests, the full applicable test suite, compileall and git diff --check. Prefer GitHub Actions Ubuntu CI evidence when a PR is created. Never claim full pass if tests or Unix dependencies cannot run in the actual execution environment.
9. Commit only code, tests and public documentation on the feature branch; check git diff/status for secrets, private applicant data, tracked production data and accidental generated files BEFORE commit. Push branch and open ONE draft PR that closes or references Issue #26 only after review; do not auto-close issue by merging. If PR creation fails, report pushed compare URL. Never commit actual candidate/HR personal data.
10. Deliver back to THIS Paperclip task: commit SHA and branch/PR URL, tests/CI status, full-coverage proof and count discrepancy outcome, list of changed files, blocked items, risks, and exact separate production approval steps. Ask Chief of Staff to QA evidence only after branch/PR exists. No new agent subtask/spend unless necessary and already authorized.

DONE means:
- Reproducible code + synthetic tests + documentation in ONE draft PR with test evidence.
- Mesabi is still not active on Hostinger.
- Any unverifiable completeness or lack of push access is clearly marked BLOCKED and not misreported as Done.

```

## Status und Sicherheit

- Das ist eine **neue ausfuehrende Paperclip-Aufgabe**, nicht die schon abgeschlossene Analyse VUT-319.
- Erwartet werden Feature-Branch, Tests, GitHub Actions und genau **ein Draft-PR**; **kein** Merge und **keine** Aktivierung auf Hostinger.
- Vor Beginn Git-Berechtigungen und dedizierten Workspace verifizieren. Falls nicht vorhanden, `BLOCKED` melden.
- Die vier Werte stehen nur fuer das **Kopieren in Paperclip** auf GitHub. Noch keine Paperclip-Ausfuehrung bestaetigt.
- Fuer alle kuenftigen Paperclip-Auftraege gilt die gemeinsame Vorlage [PAPERCLIP_TASK_FORMAT.md](PAPERCLIP_TASK_FORMAT.md).

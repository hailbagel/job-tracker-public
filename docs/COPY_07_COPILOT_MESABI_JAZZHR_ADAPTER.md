# KOPIEREN 07 – Mesabi Metallics / JazzHR Adapter

**PAPERCLIP-ERGEBNIS:** VUT-319 (21.10.2026) empfiehlt **Mesabi Metallics** als ersten weiteren Industrial-Adapter, Siemens AG nachrangig, Midrex spaeter. Diese Reihenfolge ist jetzt im [GitHub Issue #26](https://github.com/hailbagel/job-tracker-public/issues/26) erfasst.

**WICHTIGE ERGAENZUNG:** Die aktuelle oeffentliche JazzHR-Jobboerse zeigt **45 Positionen**, waehrend eine Indexansicht der offiziellen Mesabi-Karriereseite **47** anzeigt. Diese Differenz ist vor dem Produktivbetrieb zu klaeren; keine feste 45/47-Zahl im Code erwarten. Geschaeftsname: **Mesabi Metallics**, nicht das andere Unternehmen unter `mesabi.com`.

**WO EINFUEGEN:** **Betriebslaptop → VS Code → Open Folder `C:\Users\minkusp\Projects\job-tracker-public` → Copilot → Agent → Chat `Job Tracker – Development`**. Den gesamten folgenden `text`-Block in den Agent-Chat kopieren, **NICHT** ins PowerShell-Terminal und **NICHT** auf Hostinger. Kein alter Workspace/Chat erforderlich.

**WOFUER:** Einen neuen Mesabi-JazzHR-Adapter mit vollstaendigem, fehlerfestem Quellenvertrag und synthetischen Tests entwickeln. **Kein Produktionsdeploy, keine automatische Aktivierung, kein Merge**.

## Kompletten Auftrag in Copilot kopieren

```text
You are engineering lead for hailbagel/job-tracker-public on the WORK laptop in VS Code. Use the standalone project window for C:\Users\minkusp\Projects\job-tracker-public and the Copilot Agent chat "Job Tracker – Development". The old "Industrial Job Coverage" Copilot session is missing; treat the current GitHub main branch and these instructions as source of truth.

MISSION: Complete GitHub Issue #26 as a standalone draft PR:
https://github.com/hailbagel/job-tracker-public/issues/26
Implement a rigorous read-only Mesabi Metallics / JazzHR board source parser and its complete regression fixtures, but DO NOT activate Mesabi in production.

CONTEXT / EVIDENCE (21 OCT 2026):
Official Mesabi Metallics employer careers: https://www.mesabimetallics.com/careers/
Official linked employer JazzHR jobs board: https://essar.applytojob.com/
Confirmed public detail URL: https://essar.applytojob.com/apply/2tG5rSVA8x/Construction-Manager
Paperclip task VUT-319 approved Mesabi as viable first industrial candidate over Siemens AG and Midrex.
IMPORTANT potential discrepancy: public JazzHR board currently shows 45 jobs; an indexed employer careers page separately reported 47. Both are point-in-time and may have changed: reconcile fresh same-time counts/IDs when possible; never silently approve a subset or hardcode 45/47. Note that mesabi.com refers to an unrelated company, L&M Radiator, and is NOT our employer.

PRECHECK / GIT:
1. Inspect local Git status in the job-tracker-public folder. If dirty, STOP without deleting/stashing/overwriting. Preserve all private profiles, original and untracked work. If clean, git fetch origin and fast-forward main; create a NEW branch 'feature/mesabi-jazzhr-adapter'.
2. Inspect configs/sources.json, jobtracker/acquisition.py, jobtracker/pipeline.py, jobtracker/processing.py, jobtracker/registry.py, existing dvinci/personio adapter test patterns, tests, jobs_latest/job_details schema, code CI, docs/INDUSTRIAL_EMPLOYER_FEASIBILITY_2026-10-21.md, and Issue #26. Use actual implementation contracts rather than guessing.
3. Do not touch the unrelated SMS opt-in, SpaceX/Patrick ranking logic, Hostinger, Paperclip, or other feature branches.

IMPLEMENTATION:
4. Implement an adapter (e.g. jazzhr_public) using only the publicly allowed career listing and job detail pages for Mesabi Metallics Company LLC. No ATS authenticated/private API, no /cb, job application steps, robots-denied URLs, challenges, anti-bot workarounds, or external tracking. Respect robots and reasonable rate limiting for any optional one-time proof.
5. Parse board listing to collect a complete set of openings, canonical absolute detail URLs and durable opaque IDs from '/apply/<id>/...', detect duplicates or missing fields. Fetch only public details and extract title, location, job type, and substantive description fields into canonical fields. Do not invent dates, city/state for 'IA', or details absent upstream. Do not leak applicant form fields into descriptions.
6. Use existing _job(source, native_id, ...), which qualifies IDs with 'mesabi-metallics:'. Make detail validation fail closed: if list job ID not matching detail, missing/blank description required for the contract, blocked detail, invalid URL, board truncation or complete-list reconciliation failure, return status incomplete/failed and DO NOT replace last-good datasets.
7. Investigate official careers vs JazzHR count mismatch using same-time evidence. Is the official HTML rendering a different set or stale? If no independently trustworthy full count can be verified, report that and keep source in manual_discovery, not pretend verified production completeness. Any completeness claim must cite exact observed board count/unique IDs and source comparison.
8. Keep 'mesabi-metallics' source manual_discovery in configs/sources.json after this PR. If adding adapter_config or documented configuration, do not switch acquisition_mode to 'ats' or set production opt-in. No public data snapshots, no publisher allowlist change, no scheduler change, no source_status changes. SMS group stays separately default-off.
9. Add deterministic fixture tests (no live HTTP) for valid board, duplicates, same-count job turnover, partial page, altered/empty HTML, disallowed/form-only paths, invalid IDs, detail/list mismatch, missing fields, no invented timestamps, and previous last-good preservation when result incomplete. Include optional CLI read-only source probe only if necessary; ensure tests don't require network or side effects.
10. Add one brief docs explanation of coverage/ID contract, actual contemporaneous proof evidence vs uncertainty, when to consider production activation and rollback.

VALIDATION:
- Run focused tests, full available tests in the right environment, compileall, git diff --check. Windows can't import Unix-only fcntl in some publisher tests; do not hack Linux-only library.
- Commit only code, fixture-based tests and docs to the feature branch. Push normally. Create ONE DRAFT PR, reference Issue #26 and obtain Ubuntu GitHub Actions CI; address genuine CI failures on the SAME branch.
- Do not merge or deploy, no Hostinger command, no production scrape; leave repository main and host unchanged.

RETURN in a compact report:
(A) Branch/PR link, touched files and tests
(B) Board count and official website count from same-time proof, discrepancy reasons or explicit unknowns
(C) Adapter validation contract and fail-closed behaviors
(D) Ubuntu CI status, remaining limitations
(E) What separate approval/change would be required for production opt-in, bootstrap, audit and rollback.
No asking about unimportant implementation details; make good conservative decisions, stop at review boundary.
```

## Abnahme

- Eigenstaendiger Git-Feature-Branch + ein Draft-PR zu [Issue #26](https://github.com/hailbagel/job-tracker-public/issues/26)
- gruene CI/Tests, Board-Detail-ID-Abgleich, Fail-Closed bei Abweichung und Quelle bleibt `manual_discovery`
- aktuelle Mesabi-Jobanzahl unabhaengig begruendet oder als ungesichert markiert
- Keine Integration ins SpaceX-/Patrick-Ranking, keine Aenderung an SMS-Opt-in oder Hostinger.

## Weitere Prioritaeten

- Siemens AG: eigenstaendiger spaeterer Adapter (Avature, grosse Listen und HTTP-406-Zugriffsfragen).
- Midrex: Paycom-Portal, vollstaendige erlaubte Schnittstelle muss erst nachgewiesen werden.
- [SMS-Hostinger-Runbook COPY_05](COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md) und [Datenqualitaet ISSUE #24 / COPY_06](COPY_06_COPILOT_ISSUE24_RANKING_INTEGRITY.md) bleiben separate Aufgaben. **Nicht in einen PR mischen.**

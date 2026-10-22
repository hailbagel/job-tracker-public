# KOPIEREN 04 — Copilot: SMS-group-Produktivschaltung vorbereiten

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Aufgaben stehen unter [Paperclip-Tasks: vier Kopierfelder je Agent](paperclip/README.md). Nicht doppelt ausführen; kein Hostinger-Deploy.


**STATUS AM 21.10.2026:** <https://github.com/hailbagel/job-tracker-public/pull/23> wurde **erfolgreich gemergt** (Merge-Commit `b4225af`). Die Linux-CI hat bestanden. Der Adapter bleibt bewusst `manual_discovery`. **Dieser Prompt kann jetzt im bestehenden Copilot-Chat ausgeführt werden.**

**WO EINFÜGEN?** **Betriebslaptop → VS Code → derselbe Copilot-Agent-Chat `Industrial Job Coverage`**, ins Nachrichteneingabefeld. **Nicht** ins VS-Code-PowerShell-Terminal und nicht auf Hostinger.

**WOFÜR?** Copilot soll im nächsten separaten Entwicklungs-PR die technischen Voraussetzungen für echte automatische SMS-Stellenerfassung und Veröffentlichung schaffen (Bootstrap, Publisher-Allowlist, Audit, stufenweise sichere Aktivierung, Tests). **Kein tatsächlicher Produktiv-Rollout und kein eigenmächtiger Merge**. ChatGPT bewertet den PR nach Tests und entscheidet selbstständig über nächste Schritte.

## Text komplett kopieren und an Copilot senden

```text
Continue in the SAME VS Code Copilot Agent chat "Industrial Job Coverage" on the work laptop.

PR #23 HAS ALREADY BEEN MERGED into main. Confirmed merge commit: b4225afacda0afa57054cbcce6e87fe31ecfa317.
https://github.com/hailbagel/job-tracker-public/pull/23
Do not re-open or recreate PR #23. First verify that main contains the merge commit; if not, fetch and fast-forward a clean worktree.

MISSION: Prepare a separately reviewable, safe production-enablement change for SMS group; do not perform any production change.

0. SAFETY PRECHECK: Confirm this is the correct repo hailbagel/job-tracker-public and local worktree is clean. If not, STOP and ask owner. After verified PR #23 merge, git fetch origin main, git switch main and git pull --ff-only origin main. Do not reset/clean/stash private files. Create a NEW branch named feature/sms-production-enablement (or a clearly equivalent unused name); no direct changes to main.

1. READ contracts in full: scripts/publish_public_data.py (dynamic OUTPUT_ALLOWLIST and require_tracked_allowlist), scripts/audit_public_data.py (tracked-data equality), jobtracker/acquisition.py, registry.py, pipeline.py, processing.py, configs/sources.json, .gitignore, tests/test_publication.py, tests/test_public_data_audit.py, docs/public_data_publication.md, PUBLIC_REPOSITORY_POLICY.md, docs/INDUSTRIAL_EMPLOYER_FEASIBILITY_2026-10-21.md and PR #23. Do not infer that simply changing sms-group acquisition_mode to api is a safe deployment.

2. DESIGN REVIEW FIRST: The production publisher fast-forwards main automatically on each 6-hour due run; therefore MERGING an enablement PR can automatically deploy SMS on Hostinger without a separate human git pull. Publication requires all newly allowlisted output paths to be already tracked. The audit requires its exact tracked-data path set to match automated sources, so adding bootstrap files while SMS is still manual may fail the audit. Propose a safe, atomic two-phase gating mechanism (e.g. a separately controlled host opt-in flag with default disabled and tests, or an equally safe staged rollout) that preserves audit and tracked-file contract in BOTH stages. Never publish false successful acquisition metadata or invent job records. Any bootstrap must be clearly non-production with explicit status, and tests must prove the first successful source run replaces the bootstrap before publication. Preserve the complete old data and fail closed.

3. IMPLEMENTATION: Prepare an isolated PR only after reviewing that mechanism with existing code, using current normalized outputs and metadata. Ensure SMS jobs remain EXCLUDED from SpaceX/Patrick Space/Rocket contributor feeds and rankings. Add tests proving:
- all required SMS public outputs are tracked and allowlisted exactly when enabled;
- no unintended data files tracked and no unreviewed outputs committed;
- complete SMS source makes non-empty canonical current/detail/history records and coherent metadata;
- incomplete/blocked SMS acquisition preserves last-good snapshots and does not break unrelated sources;
- active history IDs equal current IDs, duplicate multilingual openings are collapsed, no fake events for identical repeated successful snapshots;
- SMS output/source_status can pass the FULL audit with 0 failures in fixture-based temp repo;
- timer eligibility, failed-attempt backoff and existing publisher remain unchanged;
- PR does not expose any private Patrick profile, secrets, sessions, cookies or credentials.

4. VERIFICATION: On Windows run targeted fixture-based checks and Python syntax checks. Under Ubuntu GitHub Actions run the complete unittest suite, publication integration tests and audit fixtures. Require tests to succeed. Do not call live Hostinger or run its publisher.

5. GIT/REVIEW: Commit only intentional code/tests/docs and reviewed non-sensitive bootstrap files on the feature branch, push normally (no force), and open ONE DRAFT PR against main using the standard GitHub path, NOT GitKraken authentication. If GitKraken prompts for authentication, cancel and return the feature branch name; PR can be created separately. DO NOT merge. DO NOT enable on Hostinger. DO NOT change or run systemd timer/service. ChatGPT is handling technical release review and merge decisions; return concrete evidence and any production-risk blockers rather than asking the owner to review code. Keep any live-enabling PR unmerged pending explicit deployment validation and an agreed low-risk rollout.

6. DELIVERABLES: Provide source enablement stages, precise GitHub PR link (or pushed branch if GitKraken refuses), CI evidence, tracked-output list, pilot success criteria, stop/rollback plan, independent Patrick feed behavior, and blockers. ChatGPT will review the result and decide next steps without routine code-review questions.

If you cannot design a safe atomic rollout because the dynamic allowlist and exact data audit contract conflict, STOP with an evidence-backed plan instead of producing a risky PR.
```

## Abnahmekriterien

- Eigener Draft PR mit grünem Ubuntu CI, nachvollziehbarer Architektur, Produktionsfreigabe-Gate und Rollback.
- Der bisherige 6-Stunden-Scheduler und alle Space/Rocket-/Patrick-Datensätze bleiben unberührt.
- Es wird NICHT versehentlich live gegangen: `main` wird vom Hostinger-Publisher automatisch fast-forwarded; bereits der Merge eines aktivierenden Codes kann ein Deployment sein.
- Die SMS-Quelle ist bis zur expliziten Operations-Freigabe nicht aktiv.
- **Midrex, Mesabi und Siemens** werden nicht unvollständig mit-aktiviert; separate Quellrecherche/PRs später.

## Vorbedingungen / Referenzen

- [Gemergter PR #23: SMS d.vinci Adapter](https://github.com/hailbagel/job-tracker-public/pull/23)
- [Linux CI #23](https://github.com/hailbagel/job-tracker-public/actions/runs/39566138965)
- [Industrial Employer Feasibility](https://github.com/hailbagel/job-tracker-public/blob/feature/industrial-sms-source/docs/INDUSTRIAL_EMPLOYER_FEASIBILITY_2026-10-21.md)

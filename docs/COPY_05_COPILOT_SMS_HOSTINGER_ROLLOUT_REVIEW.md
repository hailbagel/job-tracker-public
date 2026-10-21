# KOPIEREN 05 — Copilot bereitet SMS-Hostinger-Aktivierung vor

**STATUS:** [PR #25](https://github.com/hailbagel/job-tracker-public/pull/25) ist gemergt (Commit `daa9a08`); beide Ubuntu-Workflows sind erfolgreich. Der SMS-Adapter ist **standardmäßig ausgeschaltet**, weil auf Hostinger `JOB_TRACKER_ENABLE_SMS_GROUP=1` noch nicht gesetzt wurde.

**WO EINFÜGEN?** Auf dem **Betriebslaptop** → **VS Code → vorhandener Copilot Agent Chat `Industrial Job Coverage`** → Textbox. **Nicht** im Terminal, **nicht** auf Hostinger. Du brauchst die VS-Code-Erweiterung „GitHub Actions“ **nicht** zu installieren.

**WOFÜR?** Copilot erstellt den letzten sicheren Betriebsfahrplan für SMS group: ein schreibgeschützter Hostinger-Preflight, ein kontrollierter Opt-in-Pilot, eine Datenabnahme und ein genau definiertes Rollback. Die Befehle werden als eigene, kommentierte Kopierblöcke in der Repo dokumentiert. Er **führt selbst nichts** auf Hostinger aus. ChatGPT prüft die Ergebnisse und führt die nächsten GitHub-Schritte durch.

## Gesamten Block hieraus in Copilot Chat kopieren

```text
Continue in the SAME VS Code Copilot Agent chat "Industrial Job Coverage" on the WORK laptop.

STATUS VERIFIED: PR #25 was merged into main. Merge commit: daa9a086c9fadda413d38bb66d5168d1c34f98bd. Its source and scheduler/publisher Linux CI both passed. This adds a DEFAULT-OFF SMS group production gate (JOB_TRACKER_ENABLE_SMS_GROUP). It DOES NOT mean SMS acquisition is live on Hostinger. Existing Hostinger systemd publisher must remain intact.

YOUR TASK: Write a safe, explicit Hostinger SMS production PILOT / ROLLBACK RUNBOOK for later execution in the Hostinger Web Terminal. No live system access or production activation from VS Code. Do NOT run Hostinger commands; only prepare them in versioned docs with precise copy-paste destinations. Keep SMS out of Space/Rocket Patrick rankings.

1. Confirm GitHub main contains merged PR #25; inspect the actual implementation and all documented deployment contract files, not assumptions: configs/sources.json, jobtracker/acquisition.py, scripts/publish_public_data.py, scripts/audit_public_data.py, scripts/hostinger_scheduler_state.py, tests/test_publication.py, tests/test_public_data_audit.py, docs/public_data_publication.md and original PR #25 diff. Confirm configured env variable is disabled by default.

2. Prepare a separately copyable, READ-ONLY Hostinger PRE-FLIGHT command block which: confirms root and repo path, HEAD branch and merge ancestor without changing files, clean git worktree, installed scheduler state, exact effective service unit and drop-ins (systemctl cat and show), opt-in unset, opt-in status metadata and verified bootstrap files, git tracked SMS files, timer and service status, last successful publication, GitHub status, Python test readiness, and a read-only full data audit with understood warning categories. Command should never require printing credentials/private profiles.

3. Provide the SAFE ACTIVATION PLAN with ONE ROOT TERMINAL copy block only after pre-flight passes. It must place an isolated, reversible service override under systemd drop-in to set JOB_TRACKER_ENABLE_SMS_GROUP=1 for the publisher's actual service environment; check effective unit and that no active publication overlaps; daemon-reload; preserve existing state/6h timing, lock and 6h error backoff; do not use 'systemctl set-environment' without PassEnvironment proof and do not alter unrelated drop-ins; avoid restarts or forced immediate runs unless the eligibility gate authorizes them. Use clean idempotent checks and explicit failure path and rollback. Prefer the next due guarded service invocation.

4. Define LIVE ACCEPTANCE evidence expected after first successful opt-in collection: SMS has positive current and matching detail counts, complete acquisition metadata, source_status successful/attempted consistent, SMS normalized bootstrap replaced by real data in a published GitHub commit, audit 0 FAIL and only separately known Tesla/Jacobs warnings, historical invariants and no regression in SpaceX/Patrick counts, scheduler timer still running. Verify sitemap/feed equivalence and source provenance only to degree supported by adapter.

5. Include ONE rollback copy block that removes ONLY the dedicated SMS opt-in drop-in, reloads systemd safely, leaves published last-good snapshots untouched, records failure and restores normal six-hour scheduling. If failure of source collection occurs, do not invent data, do not switch to bypass scraping. If real logs show publisher failing unrelated sources, halt pilot and report.

6. Document warnings to owner: PR #25 merge is code/bootstrap only. GitHub Actions success is not live Hostinger verification. The opt-in is not set. No additional full production run has been verified after this merge. Never assert that SMS is live until production metadata and audit prove it.

7. Do not modify any existing code, tracker data, config or Hostinger units. Create only new docs / an optional static non-executable check script and tests in a clean, dedicated docs branch if needed. Do not branch if local worktree dirty; preserve all private local files. git fetch and fast-forward clean main before branching. Push changes to a review branch and return its name and GitHub link; if GitKraken auth/browser blocks PR creation, do NOT reauthenticate, report branch only; ChatGPT can create the PR. DO NOT merge a PR or deploy.

OUTPUT: concise report with runbook path, exact read-only pre-flight block, pilot activation block, rollback block, risk list, CI/tests if any, feature branch link and outstanding physical Hostinger checks. Owner does not do code review; return verifiable results for ChatGPT to review.
```

## Abnahme

- Eine neue Markdown-Runbookdatei im `docs/`-Ordner mit exakt bezeichneten Kopierblöcken für **Hostinger Web Terminal** und transparenten Vorbedingungen.
- Separater Branch/PR für Dokumentation; keine Änderung an `main`, `data/`, dem bestehenden Scheduler oder Hostinger durch Copilot.
- Nach Prüfung übernimmt ChatGPT den weiteren GitHub-Workflow. Die Hostinger-Befehle werden erst nach validiertem Runbook vom Operator ausgeführt.

## Links

- [Gemergter PR #25](https://github.com/hailbagel/job-tracker-public/pull/25)
- [Industrie-CI erfolgreich](https://github.com/hailbagel/job-tracker-public/actions/runs/39573766873)
- [Scheduler-CI erfolgreich](https://github.com/hailbagel/job-tracker-public/actions/runs/39573766773)

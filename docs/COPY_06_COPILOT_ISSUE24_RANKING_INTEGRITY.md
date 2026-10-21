# KOPIEREN 06 — Issue #24: Ranking-IDs gegen aktuelle Jobdaten pruefen

**STATUS:** [Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24) ist eine offene Entwicklungsaufgabe, kein laufender Hostinger-Fehler. Der alte [PR #17](https://github.com/hailbagel/job-tracker-public/pull/17) wurde als ueberholt geschlossen; canonical audit: `scripts/audit_public_data.py`.

**WOFUER?** Unabhaengiger Abgleich von Patrick- und SpaceX-Ranking-IDs gegen tatsaechlich aktuelle Quelldaten. Ausgetauschte Stellen bei gleicher Gesamtzahl muessen erkannt werden.

**WANN?** Separat NACH der [SMS-Hostinger-Runbook-Aufgabe 05](COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md), oder wenn diese explizit zurueckgestellt wird. Keine Aufgaben vermischen.

**WO EINFUEGEN?** Auf dem BETRIEBSLAPTOP in **VS Code → Copilot → Agent-Chat "Industrial Job Coverage"**; den ganzen folgenden Textblock einfügen. **NICHT in PowerShell / Hostinger**.

## Kompletten Copilot-Auftrag kopieren

```text
You are working in the existing VS Code Copilot Agent chat "Industrial Job Coverage" on the company laptop, but this task is a separate narrowly scoped Data Quality work package for GitHub Issue #24:
https://github.com/hailbagel/job-tracker-public/issues/24

DO NOT begin until the SMS group rollout pre-flight/runbook handoff (COPY_05) has been delivered or explicitly paused. Never mix source enablement and data-integrity changes in the same PR.

OBJECTIVE
Fix the canonical read-only auditor scripts/audit_public_data.py so that a ranking containing stale IDs is rejected even when its row count is unchanged and Patrick JSON/CSV ordering and metadata match.

BEFORE YOU START
1. Open existing local repo hailbagel/job-tracker-public. Ensure worktree clean. Preserve private files: no reset, git clean, force push or stash.
2. Fetch origin/main, switch main and fast-forward ONLY. Create NEW feature branch fix/issue24-ranking-id-audit. Do not use old SMS branch.
3. Read Issue #24 and scripts/audit_public_data.py, jobtracker/patrick.py (_public_record, _source_rows, generate_multi), analysis/profile_ranking.py, jobtracker/registry.py, configs/sources.json, data/source_status.json, tests/test_public_data_audit.py, docs/public_data_publication.md, PUBLIC_REPOSITORY_POLICY.md.
4. DO NOT revive/merge PR #17; canonical auditor already validates Patrick contributors from registry and detail IDs/links together by source row. Preserve this.

IMPLEMENTATION
- Independently derive expected source-qualified current job IDs from successful configured eligible Space/Rocket Patrick contributors' current jobs_latest.csv, and the SpaceX-only feed from current SpaceX jobs_latest.csv. Respect the same stable native ID qualification used by the real producer (source-id:native-id); confirm fields in source before coding. Do not trust only publication counts/feed's own metadata.
- Verify actual ranked IDs equal independently derived current IDs: reject duplicates, missing/extra/foreign IDs and wrong source qualification. Compare as sets/multisets without requiring ranking relevance order to match source input order; preserve existing JSON/CSV ordered-pair check.
- Independently validate SpaceX-only feed. Never mix SMS Industrial jobs into Patrick Space/Rocket ranking.
- Do not classify last-good Tesla/Jacobs snapshots as fresh; preserve contributor fail-closed semantics. Test source namespace collision, blank/malformed IDs, 0-row edges.
- Audit READ ONLY. NO data/, configs, source_status, scheduler/systemd, publisher, profiles or secrets changes. NO running scrapers.
- Add fixture regressions: same-count job turnover (FAIL), valid current (PASS), duplicate/missing/extra/foreign ID (FAIL), JSON/CSV mismatch (FAIL), same native ID at different contributors is distinct, omitted required contributor (FAIL), swapped ID/link detail pairing (FAIL). Fixture-based and deterministic; explain performance at large live snapshot.
- Do not change public feed schema, sorting, output or publisher code to make tests pass.

VALIDATION AND GIT
Run targeted audit tests, compileall, git diff --check and full Ubuntu GitHub Actions suite. Windows fcntl is Unix-only; do not hack production. Repair CI failures using real logs on same branch.
Commit only code/tests/docs, push normally and open ONE DRAFT PR referencing Issue #24. If GitKraken asks login, cancel and return branch name; ChatGPT can create PR. No merge/deploy/Hostinger commands.

DELIVERABLE
Concise source-to-feed reconciliation method, negative test proof, Linux CI outcome/links, draft PR URL or pushed branch, risks and later read-only post-deploy audit. Stop at PR review boundary.
```

## Abnahme

Fokussierter Draft-PR zu Issue #24, gruene Ubuntu CI, positive und negative Test-Fixtures, keine Produktionsdaten- oder Hostinger-Aenderung. ChatGPT prueft den PR.

## Kontext

- [PR #21](https://github.com/hailbagel/job-tracker-public/pull/21): History-Invariante.
- [PR #25](https://github.com/hailbagel/job-tracker-public/pull/25): SMS standardmaessig abgeschaltet.
- [PR #17](https://github.com/hailbagel/job-tracker-public/pull/17): alter Audit-Ansatz, nicht mergen.

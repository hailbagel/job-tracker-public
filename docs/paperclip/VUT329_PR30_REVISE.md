# VUT-329 – vorhandenen PR #30 revidieren, kein neuer Task

**Status 22.10.2026:** Nicht auf **Accept code review**, sondern **Revise** klicken. Die lokale Frischeprüfungslogik mit `STALE_AFTER=2*MINIMUM_INTERVAL=12h` besteht ihre 13 Tests. Beide vollständigen Linux-CIs auf Draft-PR #30 sind jedoch fehlgeschlagen, weil `tests/test_publication.py:164` noch die veraltete SMS-Dateiliste erwartet. [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) behebt dies bereits, ist aber noch nicht in `main`.

## WO EINFÜGEN?

In Paperclip → VuTruLabs → **bestehender Task VUT-329** → Confirmation Pending → **Revise** → Begründung einfügen. **Nicht** `New Task`. Nur **ein** Copy-Block für die bestehende Review-Revidierung (kein neuer Task mit Title/Assignee/Project).

## Revise – kopieren

```text
REVISE — VUT-329 / EXISTING DRAFT PR #30 ONLY

The code review cannot be accepted yet. Both latest Ubuntu GitHub Actions checks on PR #30 FAILED:
- Industrial source Linux CI: https://github.com/hailbagel/job-tracker-public/actions/runs/39791151245
- Hostinger scheduler Linux review: https://github.com/hailbagel/job-tracker-public/actions/runs/39791145578

Focused 13 scheduler tests, systemd syntax and six-to-twelve-hour staleness boundary tests passed, but BOTH workflows fail the SAME old unscoped tests/test_publication.py:164 assertion, which incorrectly expects an earlier SMS PR's exact changed-file list. The equivalent security test was already repaired in green CI on draft PR #29 (unmerged), so this is a cross-PR integration dependency, not evidence that the scheduler change is broken.

Please make ONE bounded correction to the EXISTING PR #30 branch. Prefer merging PR #29 only AFTER its separately authorized review/merge, then update PR #30 from main. If PR #29 cannot be merged yet, port ONLY its independently reviewed PR-independent sensitive-path regression test into PR #30, preserving all security checks. Do not remove/skip/weaken the test or substitute a new hard-coded file list. Do not create another task, PR, or branch.

Rerun BOTH GitHub Actions workflows until green, report exact commit SHA and links. Keep PR #30 DRAFT; require independent code acceptance. No Hostinger access/production change is authorized. Effective host revision, persistent scheduler state after reboot and last three independent scheduled six-hour successes remain UNVERIFIED and require separate read-only operator evidence and later operational acceptance.
```

## Nachweise und Abnahme

- GitHub: [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30), [Kommentar mit CI-Root-Cause](https://github.com/hailbagel/job-tracker-public/pull/30#issuecomment-6342685150).
- [Run 39791151245: failed](https://github.com/hailbagel/job-tracker-public/actions/runs/39791151245), [Run 39791145578: failed](https://github.com/hailbagel/job-tracker-public/actions/runs/39791145578).
- Beide Fehler: alter `test_pull_request_changes_only_reviewed_non_sensitive_paths`, nicht die neuen Scheduler-Tests.
- Code-Abnahme und Hostinger-Betriebsabnahme sind **unabhängig**. Ohne neue Hostinger-Journale keine Behauptung von 3 geplanten erfolgreichen Sechs-Stunden-Läufen.

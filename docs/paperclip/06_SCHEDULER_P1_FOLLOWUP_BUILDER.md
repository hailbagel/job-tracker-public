# PAPERCLIP TASK – JT-SCHEDULER-P1: PR #30 Health Check Harden

**Status:** NEXT. **Wo einfügen:** Paperclip → VuTruLabs → Tasks → New Task. Alle **vier Felder getrennt kopieren**, keinen VS Copilot verwenden. Dies ist ein **neuer klar begrenzter Follow-up zu zwei bisher nicht behobenen GitHub P1 Reviewbefunden**, kein Duplikat der abgeschlossenen VUT-329-Arbeit und **kein neuer GitHub-PR**.

## Title
```text
JT-SCHEDULER-P1 – Fix false OK on failed attempt / stopped timer in PR #30
```

## Assignee
```text
Builder
```

## Project
```text
Job Tracker Public
```

## Prompt
```text
ROLE: Builder / engineering owner, work in the existing public GitHub repository hailbagel/job-tracker-public.

OBJECTIVE: Address BOTH unresolved P1 code-review findings on the EXISTING PR #30 ("Align scheduler freshness check with six-hour cadence"). This is a narrow follow-up to completed Paperclip VUT-329, NOT an alternative implementation or a new PR.

CONTEXT:
- GitHub PR: https://github.com/hailbagel/job-tracker-public/pull/30
- Branch: fix/vut-329-scheduler-freshness
- Current head: c0bc28196c87c3be8171639690ae026f743b9b5b
- Both Linux CI workflows passed on this commit, but the code review found two unacceptable false-OK health checks. Existing CI green is not enough.
- Independent actionable PR comment: https://github.com/hailbagel/job-tracker-public/pull/30#issuecomment-6348771538
- Check PR/head/current tasks before editing. If another writer currently works on PR #30, report BLOCKED and do not race.

TASK A — failed last publisher attempt:
scripts/check_hostinger_scheduler.py currently logs a more recent last_attempt_status="failed" but can still return 0 while last_success_utc is younger than 12 hours. This must be a nonzero health status if the latest attempt failed AFTER the last successful execution. Avoid false alerts when an older failure was followed by a later verified success; preserve existing started/ongoing semantics and readable diagnostics. Do not confuse publication eligibility, six-hour retry backoff and health.

TASK B — non-operational timer:
The check prints systemctl show timer ActiveState but currently never acts on it. Validate that vutrulabs-job-tracker-public.timer is actually active and fail closed on inactive, failed, missing or unparseable state. A systemd oneshot publisher SERVICE being inactive between runs is NORMAL and must not trigger a failure on its own. Preserve read-only systemd operations only; no start/stop/restart.

TESTS:
- recent prior success + newer failed attempt => nonzero
- older failed attempt + later confirmed success => healthy
- timer inactive/failed/unrecognized => nonzero even when last success is fresh
- active timer + success younger than 12h => healthy
- normal inactive oneshot service => healthy if timer/state otherwise healthy
- preserve last-success age boundary: exactly 12h valid, >12h stale
- preserve existing startup and clock-skew checks and sensitive-path PR test
- full project Ubuntu GitHub Actions workflows BOTH green; python compileall; git diff --check; update read-only operations documentation as needed.

DELIVERABLE:
1. Commit/push ONLY to the current PR #30 branch and preserve its original scope.
2. Report changed files, new SHA, two successful CI run links, regression test names/results, remaining limitations.
3. Request independent code review only after both workflows pass.
4. Keep PR #30 unmerged until a separate owner release decision. PR #29 must be separately approved/merged in a controlled order before final production rollout.
5. NO Hostinger login, collection, production data changes, systemd activation, GitHub merge, private profile, secret access, new PR, new branch or duplicate task. If blocked, report a concrete BLOCKED result rather than declaring completion.

DONE means BOTH P1 findings are demonstrably fixed and both full Ubuntu CIs are green, NOT that the production monitor was deployed. Hostinger operating evidence and 3 scheduled successes remain a separate approval gate.
```

## Abnahme / Reihenfolge

**P0:** PR #29 eigenständig fachlich reviewen und erst nach Eigentümer-Freigabe mergen. **P1:** P1-Folgeauftrag zu PR #30 (dieser Task) beenden, unabhängiger Review, Merge nach Freigabe. **P2:** Hostinger separat abnehmen, erst dann Ranking-ID-Audit/Quellerweiterungen.

**Achtung:** Erstellte GitHub-Datei ist eine Anleitung, keine automatisch gestartete Paperclip-Ausführung.

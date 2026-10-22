# VUT-329 / PR #30 – TECHNISCHE AUSFÜHRUNG, nicht erneut Review beantragen

**Aktualisiert 22.10.2026:** Paperclip hat die frühere Entscheidung `Revise` als **rejected confirmation** ohne konkrete Änderungsforderung interpretiert. Engineering Operations hat den Task wieder zurück zur Ausführung erhalten. Deshalb **nicht erneut „Revise“ oder „Accept“ wählen und keinen neuen Task erstellen**. Direkt im bestehenden **VUT-329 → Message Engineering Operations** die folgende Anweisung einfügen. Der beauftragte Engineering-Agent soll den bisherigen Builder zur Codeänderung nutzen, falls er selbst keine Schreibrechte hat.

**GitHub-Status verifiziert:** [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30) Draft und nicht gemergt, beide CI-Workflows rot ([Run 39791151245](https://github.com/hailbagel/job-tracker-public/actions/runs/39791151245), [Run 39791145578](https://github.com/hailbagel/job-tracker-public/actions/runs/39791145578)). [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) weiterhin Draft, beide CI-Workflows grün. Die Korrektur ist dort bereits in `tests/test_publication.py` vorhanden. **Keine Produktionsfreigabe.**

## Nachricht für bestehenden VUT-329 – EINZELN KOPIEREN

```text
VUT-329 — EXECUTE THE FIX NOW, NOT ANOTHER REVIEW REQUEST

The previous "Revise" response was registered as a rejected confirmation without an actionable technical change request. This is the actionable request for the EXISTING task VUT-329 and EXISTING draft PR #30.

Engineering Operations: assign the actual code correction to the existing capable Builder through this same task/existing handoff. Do NOT create a new issue, task, branch, or PR. Do NOT request human acceptance again until CI is green.

Repo: hailbagel/job-tracker-public
PR: https://github.com/hailbagel/job-tracker-public/pull/30
Branch: fix/vut-329-scheduler-freshness
Blocking CI runs: 39791151245 and 39791145578

CAUSE: PR #30 has only the three expected scheduler files, but tests/test_publication.py:136-164 on the base/main unconditionally asserts a hardcoded list of old SMS PR files. Both Linux workflows fail that one unrelated test. The already reviewed draft PR #29 has the exact PR-independent security-sensitive-path test fix at tests/test_publication.py:136-157, and two passing workflows (39788298467 and 39788298466).

ACTION:
1. On PR #30's EXISTING branch only, port the reviewed PR-independent sensitive-path regression guard from PR #29's tests/test_publication.py. Keep checks for sensitive path terms (private_profiles, credentials, secrets, cookies, sessions), .env and .env.* excluding .env.example, and private key/cert suffixes (.key/.pem/.p12/.pfx). Remove the unrelated fixed SMS file-list requirement. Do not delete/skip/loosen the safety test.
2. Preserve the new six-hour-cadence monitor and its 13 focused tests; do not change the production scheduler, systemd units, or any Hostinger configuration.
3. Run the full Linux test suites on the EXISTING PR #30, compileall and git diff --check; push the correction only to its existing branch. Report new SHA and links to BOTH successful CI runs. If blocked by access/CI, report the exact blocker and stop — do not mark done.
4. Only AFTER both checks are green, request one independent CODE review of PR #30. Keep PR Draft. Separate operational acceptance still needs real Hostinger journal evidence, installed revision, persistent state and three independent scheduled 6-hour runs. Do not attempt Hostinger, deploy, publish or merge.

This is a concrete engineering execution instruction, not approval for merge or production.
```

## Wie geht es weiter?

1. In Paperclip den bestehenden Task **VUT-329** öffnen und **oben stehende Nachricht** an **Engineering Operations** senden, nicht in den Board-Confirmation-Dialog.
2. EO beauftragt seinen vorhandenen Builder oder führt die enge Korrektur selbst aus. **Kein neuer Task, kein neuer PR**.
3. Beide Ubuntu-CIs vollständig grün => erst dann ein erneutes Code-Review. Die **Hostinger-Abnahme bleibt separat**.
4. Bei fehlenden Zugriffsrechten, nicht erreichbarem Builder oder erneutem leeren Review-Kreis: **konkreten Blocker melden**, nicht `Done` markieren.

**Hinweis:** Ein Repo-Commit dokumentiert diese Anleitung, übermittelt sie aber nicht automatisch an Paperclip. Eine GitHub-PR-Diskussion allein löst den Paperclip-Task nicht aus.

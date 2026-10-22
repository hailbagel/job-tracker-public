# VUT-328 / PR #29 – Wiederaufnahme ohne doppelten Task

**Stand: 22. Oktober 2026, GitHub Actions geprüft.**

## Was nachgewiesen ist

- Paperclip **VUT-328** (Builder) wurde für den RFA-GREEN-Fix bereits ausgeführt, ist jedoch aufgrund einer **missing disposition / board decision required** blockiert. **VUT-331** ist davon abhängig. Keine dieser Aufgaben neu erstellen.
- **VUT-332** (Chief of Staff, Read-only-Top-10-QA) ist **Done**: unter zehn geprüften Positionen **5 überprüfte Evidenzmängel**, **4 nicht verifizierbare Quellen**, **1 materiell stimmiger Datensatz**. Nur diese Stichprobe, keine Gesamtquote. RFA-IDs 4944174101 und 4997134101 zeigen falsche GREEN-Evidenz in der alten veröffentlichten Momentaufnahme.
- Bestehender [Draft PR #29](https://github.com/hailbagel/job-tracker-public/pull/29), Branch `fix/vut-328-greenhouse-requirements`, Commit `2c9c7d7d`: Implementierung existiert. RFA-Regressionstests bestanden, **volle Ubuntu-Suite 119/120 bestanden, ein Fehler**.
- Fehler [Actions Run 39748067427](https://github.com/hailbagel/job-tracker-public/actions/runs/39748067427): `tests/test_publication.py:164` hat eine hartkodierte **veraltete SMS-PR-Dateiliste** mit `assertEqual(expected, changed)` auf jedem PR. PR #29 ändert hingegen nur `jobtracker/acquisition.py`, `analysis/profile_ranking.py`, `tests/test_greenhouse.py`. Das ist der CI-Blocker; kein Testbeleg gegen den neuen RFA-Parser.
- [Detaillierte GitHub-Korrekturanweisung direkt in PR #29](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6341914957).

## 1. Berechtigte Board-Entscheidung in der BESTEHENDEN Paperclip-Aufgabe VUT-328

**WO EINFÜGEN:** Paperclip → VuTruLabs → bestehende **VUT-328** öffnen → Nachricht an **Builder** bzw. Board-Recovery-Entscheidung. **Nicht** `New Task`. Ein Chatkommentar allein behebt ggf. die technische Disposition nicht: die vorgesehene Board-Recovery-Aktion muss ein berechtigter Owner separat bestätigen.

### Nachricht an den bestehenden Builder / das Board

```text
OWNER DECISION — VUT-328 RECOVERY / PR #29

Approve a SINGLE bounded continuation of the EXISTING Builder task VUT-328, by the original assigned Builder, on the EXISTING draft PR #29 and branch fix/vut-328-greenhouse-requirements. Do not create a duplicate task, branch, implementation or PR. This approval covers only the CI/acceptance regression fix. It does NOT authorize merge, deployment, Hostinger changes or secrets/private profile access.

Verified root cause: GitHub Actions run 39748067427 fails 1 of 120 tests. tests/test_publication.py:164 unconditionally asserts a stale hard-coded SMS PR file set. It must be made PR-independent while retaining meaningful private/sensitive path restrictions. Do not simply skip/remove the test or add new RFA paths to an old SMS list. Keep SMS-specific exact-path assertions only in properly scoped SMS-specific tests.

Execute one controlled correction and rerun the full Ubuntu CI suite, focused Greenhouse/Green checks, compileall and git diff --check on the SAME branch. Preserve test coverage for RFA 4944174101 and 4997134101, including UNKNOWN when requirements are missing/unverified and positive fully evidenced GREEN controls. Report commit, links, full CI result and any remaining blockers. Keep PR in Draft until independent acceptance.

Board: resolve the existing missing_disposition/clear_next_step recovery for VUT-328 so the original Builder can resume. VUT-331 remains blocked until VUT-328 produces green CI evidence.
```

## 2. Nicht tun

- Keine neuen CTO-/Builder-Tasks zur selben RFA-Codeänderung.
- Keine direkte Änderung auf Hostinger, kein Merge/Produktivdaten-Refresh.
- Keine Änderung an `main` für diesen Testfix. **PR-Branch #29 ist die einzige Implementierungsstelle**.
- Paperclip-Berechtigungs-/Dispositionsblocker nicht als erledigt erklären, solange das Board ihn nicht bestätigt.

## 3. Abnahme

Nach erfolgreicher CI im bestehenden PR #29 VUT-328-Abnahmebelege prüfen und erst dann VUT-331 entblocken. F2 (6-h-Monitor) und F3 (Ranking-ID-Audit) bleiben getrennte nachgelagerte Arbeiten.

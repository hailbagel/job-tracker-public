# START HIER – Job Tracker / Paperclip

> **Verifizierter Stand 24.10.2026**: RFA PR #29 auf Head `6af2058d055e0d85d999a6f8f526f00ec18c6d3c`. Paperclip VUT-345 done, unabhängige VUT-347 QA PASS (laut Abschlussbericht). Zwei Ubuntu Linux-CIs auf diesem Head grün: [Industrial](https://github.com/hailbagel/job-tracker-public/actions/runs/39959242638), [Scheduler](https://github.com/hailbagel/job-tracker-public/actions/runs/39959241886). **PR #29 ist Ready for review und nicht gemergt.** [Abnahmekommentar/Limitations](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6381219564). Fünf ältere Codex-Review-Threads sind noch offen markiert: konkret gegen neuen Code + Tests prüfen, nicht blind abnicken, aber auch keine weiteren pauschalen Refactor-Schleifen.

## NÄCHSTE SCHRITTE (keine neuen Paperclip Tasks)
1. PR #29: Auf aktuellem Head Review-Threads abschließend reconciliieren, Merge-Voraussetzungen bestätigen; **separater Merge-Entscheid**. Kein Code/Hostinger-Deploy ohne Freigabe.
2. PR #30: 6h-Monitor auf Head `9238944`, [Industrial CI grün](https://github.com/hailbagel/job-tracker-public/actions/runs/39837694307), [Hostinger CI grün](https://github.com/hailbagel/job-tracker-public/actions/runs/39837694272). Erst nach PR #29 kontrolliert auf neues `main` synchronisieren, beide CIs erneut laufen lassen, Review-Threads prüfen, gesonderte Merge-Entscheidung.
3. Danach Hostinger-Laufzeitstand nachweisen: installierte Revision, Timer-Journal, persistenter State, drei getrennte erfolgreiche planmäßige 6h-Läufe. Kein Produktionszugriff in einem reinen PR-Review.
4. Ranking-ID-Audit [Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24) abschließen; erst dann wieder Quelleinbindung/SMS/Mesabi priorisieren.

**Abgeschlossene Paperclip Tasks nicht duplizieren**: VUT-328,329,331,332,335,341,344,345,347. [Taskindex](docs/paperclip/README.md) ist das Archiv mit getrennten Kopierfeldern. PR #29: nur sachlich belegte neue P1-Risiken rechtfertigen weiteren Builder-Auftrag.

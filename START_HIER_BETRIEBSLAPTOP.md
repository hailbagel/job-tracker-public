# START HIER – Job Tracker / Paperclip

> **Aktueller Stand 22.10.2026:** Paperclip zeigt VUT-328/329/331/332 als **Done**. GitHub PR #29 noch **Draft**, PR #30 **open** und beide **nicht gemergt**. Beide haben je 2/2 grüne Ubuntu-CIs, aber **PR #30 besitzt 2 bislang ungelöste P1-Code-Reviewbefunde** (false-OK bei letztem Fehlversuch oder gestopptem Timer). Daher **noch keine Merge-/Produktionsfreigabe**.

## JETZT: ein Paperclip-Builder-Folgeauftrag

**[Task 06 – PR #30 P1 Health-Check-Fix, vier getrennte Kopierboxen](docs/paperclip/06_SCHEDULER_P1_FOLLOWUP_BUILDER.md)**

Der neue Task bezieht sich auf den **bestehenden** PR #30, Branch `fix/vut-329-scheduler-freshness`. **Keinen neuen GitHub-PR/Branch** erstellen; VUT-329 nicht duplizieren. [Belegte Reviewer-Findings](https://github.com/hailbagel/job-tracker-public/pull/30#issuecomment-6348771538).

## RELEASE-Reihenfolge

1. PR #29 fachlich unabhängig prüfen und nur nach Eigentümerfreigabe mergen.
2. PR #30 P1-Reparatur; beide CIs erneut grün + unabhängiger Review; Integration nach Freigabe.
3. Hostinger-Version / Journale / Zustand / drei geplante erfolgreiche 6-h-Läufe separat prüfen. Ohne Hostinger-Belege keine Produktionsabnahme.
4. Danach [Ranking-ID-Audit Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24), anschließend Quelle Mesabi/SMS erst nach Qualitätssicherung.

[Zentraler Paperclip-Index](docs/paperclip/README.md) mit allen Aufträgen. Neue Tasks haben `Title`, `Assignee`, `Project`, `Prompt` als vier separat kopierbare Felder. Alte VS-Copilot-Dateien sind Archiv.

# Job Tracker – Paperclip-Agenten-Aufträge

> **NEUER CODE-REVIEW-FUND zu PR #29 (22.10.2026):** Zwei nachprüfbare Randfälle: zusätzlicher unbekannter Pflichtpunkt trotz erkannter Qualifikation → potenziell falsches GREEN; ausschließlich Preferred-Qualifikationen → fälschliches hartes Gate. [GitHub-Kommentar](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6349563992). **[Genau EIN gezielter Paperclip Builder-Folgeauftrag mit 4 Copy-Boxen](07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md)**. Bestehenden PR #29 korrigieren, nicht neu implementieren. Kein Merge vor unabhängiger Prüfung.

> **NEUE PRIORITÄT – 22.10.2026:** VUT-328/329/331/332 sind laut Paperclip abgeschlossen; PR #29 und PR #30 sind jedoch ungemergt. **PR #30 hat zwei offene P1-Codex-Reviewbefunde trotz 2/2 grüner CI.** [JETZT genau ein neuer Builder-Folgeauftrag für denselben PR](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md). [GitHub-P1-Belege](https://github.com/hailbagel/job-tracker-public/pull/30#issuecomment-6348771538). **Kein Merge/Hostinger-Deploy.**

> **Historischer Stand:** Die frühere VUT-329-Revise-Schleife wurde gelöst; die unten dokumentierten Altstände sind überholt. Aktuelle Freigabekriterien stehen oben.

## Bestehende Tasks und Reihenfolge

| Priorität | Paperclip-Auftrag | Zuständigkeit | Tatsächlicher Stand |
|---|---|---|---|
| P0 | [RFA GREEN-Gate – PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) | VUT-328 / VUT-331 Done | **Draft; grüne CI; unabhängiger Codex-Review am 22.10. angefragt, noch keine Freigabe** |
| P1 | [6-h-Monitor – PR #30](https://github.com/hailbagel/job-tracker-public/pull/30) | VUT-329 Done / VUT-335 Done | **P1-Fixes implementiert; Head `9238944`; unabhängiger Review läuft; nicht gemergt** |
| QA | [Top-10-Quellenprüfung](02_TOP10_QA_CHIEF_OF_STAFF.md) | VUT-332 Chief of Staff | **Done:** 5 Evidenzmängel, 4 unverifizierbar, 1 materiell stimmig (nur 10er-Sample) |
| Danach | [Ranking-ID-Integrität](04_RANKING_ID_INTEGRITY_CTO.md) | CTO, separater Task nach Abgleich bestehender Tasks | Noch nicht als neuer Task ausführen, bevor laufende Arbeiten sauber zugeordnet |
| Pausiert | [Mesabi Metallics](05_MESABI_PAUSED_CTO.md) | CTO | Quellenwachstum bis Quality-Gate aufschieben |

## Bereits erledigter Agentenauftrag

**[VUT-335 – Scheduler P1 Follow-up](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md)** wurde in Paperclip erstellt und vom Builder am 22.10. als DONE gemeldet. **Nicht erneut erstellen oder kopieren.** Der weitere Gate ist unabhängiger Code-Review / finale CI, dann getrennte Freigabe beider PRs.

## Noch offener PR #29 Quality-Fix

[Task 07 – mandatory coverage + preferred-only parse](07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md). Nur einmal anlegen; der vorherige VUT-328 Task ist abgeschlossen. Kein zweiter GitHub PR. Bei laufender Branch-Bearbeitung zuerst koordinieren.

## Neue Aufgaben in Paperclip

**Nur wenn eine Aufgabe wirklich noch nicht existiert:** Paperclip → VuTruLabs → Tasks → New Task. Jede eigenständige Task-Datei enthält vier einzeln kopierbare Felder `Title`, `Assignee`, `Project`, `Prompt`. Alte `docs/COPILOT_*.md` sind Archiv und kein aktiver Auftrag.

**Bestehende Aufgaben nicht duplizieren.** Änderungen nur in isoliertem Branch/Task. Kein autonomer Merge/Hostinger-Deploy, keine Bewerber-Privatdaten, keine Produktionsveröffentlichung. CI-Abnahme und Hostinger-Betriebsabnahme sind unabhängig.

[Verbindliches Schema](../PAPERCLIP_TASK_FORMAT.md) · [Ursprünglicher CEO-Audit](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

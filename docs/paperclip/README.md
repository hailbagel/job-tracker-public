# Job Tracker – Paperclip-Agenten-Aufträge

> **NEUE PRIORITÄT – 22.10.2026:** VUT-328/329/331/332 sind laut Paperclip abgeschlossen; PR #29 und PR #30 sind jedoch ungemergt. **PR #30 hat zwei offene P1-Codex-Reviewbefunde trotz 2/2 grüner CI.** [JETZT genau ein neuer Builder-Folgeauftrag für denselben PR](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md). [GitHub-P1-Belege](https://github.com/hailbagel/job-tracker-public/pull/30#issuecomment-6348771538). **Kein Merge/Hostinger-Deploy.**

> **Historischer Stand:** Die frühere VUT-329-Revise-Schleife wurde gelöst; die unten dokumentierten Altstände sind überholt. Aktuelle Freigabekriterien stehen oben.

## Bestehende Tasks und Reihenfolge

| Priorität | Paperclip-Auftrag | Zuständigkeit | Tatsächlicher Stand |
|---|---|---|---|
| P0 | [RFA-Pflichtanforderungen / GREEN-Gate](01_RFA_REQUIREMENTS_CTO.md) | VUT-328 Builder / VUT-331 CTO | **Done in Paperclip** – PR #29 Draft, 2/2 CI grün, separates unabhängiges PR-Review fehlt |
| P1 | [6-h-Scheduler-Monitor](03_SIX_HOUR_MONITOR_CTO.md) | VUT-329 Engineering Operations | **Done in Paperclip** – PR #30 offen, 2/2 CI grün, aber 2 offene P1-Reviewbefunde |
| QA | [Top-10-Quellenprüfung](02_TOP10_QA_CHIEF_OF_STAFF.md) | VUT-332 Chief of Staff | **Done:** 5 Evidenzmängel, 4 unverifizierbar, 1 materiell stimmig (nur 10er-Sample) |
| Danach | [Ranking-ID-Integrität](04_RANKING_ID_INTEGRITY_CTO.md) | CTO, separater Task nach Abgleich bestehender Tasks | Noch nicht als neuer Task ausführen, bevor laufende Arbeiten sauber zugeordnet |
| Pausiert | [Mesabi Metallics](05_MESABI_PAUSED_CTO.md) | CTO | Quellenwachstum bis Quality-Gate aufschieben |

## Nächste neue Aufgabe (nicht VUT-329 duplizieren)

**[06_SCHEDULER_P1_FOLLOWUP_BUILDER.md](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md)** – Builder folgt den zwei neuen P1-Reviewbefunden im bereits vorhandenen PR #30. **Vier getrennte Kopierfelder**, kein neuer GitHub-PR. Parallel kein weiterer Agent am selben Branch.

## Neue Aufgaben in Paperclip

**Nur wenn eine Aufgabe wirklich noch nicht existiert:** Paperclip → VuTruLabs → Tasks → New Task. Jede eigenständige Task-Datei enthält vier einzeln kopierbare Felder `Title`, `Assignee`, `Project`, `Prompt`. Alte `docs/COPILOT_*.md` sind Archiv und kein aktiver Auftrag.

**Bestehende Aufgaben nicht duplizieren.** Änderungen nur in isoliertem Branch/Task. Kein autonomer Merge/Hostinger-Deploy, keine Bewerber-Privatdaten, keine Produktionsveröffentlichung. CI-Abnahme und Hostinger-Betriebsabnahme sind unabhängig.

[Verbindliches Schema](../PAPERCLIP_TASK_FORMAT.md) · [Ursprünglicher CEO-Audit](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

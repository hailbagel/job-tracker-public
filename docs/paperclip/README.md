# Job Tracker – Paperclip-Agenten-Aufträge

> **OPERATIVER STAND 22.10.2026:** [**VUT-329 / PR #30 – konkrete Engineering-Ausführungsanweisung**](VUT329_PR30_REVISE.md). Paperclip hat `Revise` als Review-Ablehnung verbucht, Task ist wieder bei Engineering Operations. **Jetzt denselben Task zur Codekorrektur ausführen**, erst bei grüner CI neues Review. Keine neue Aufgabe.

## Bestehende Tasks und Reihenfolge

| Priorität | Paperclip-Auftrag | Zuständigkeit | Tatsächlicher Stand |
|---|---|---|---|
| P0 | [RFA-Pflichtanforderungen / GREEN-Gate](01_RFA_REQUIREMENTS_CTO.md) | VUT-328 Builder / VUT-331 CTO | Draft [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29), CI **grün**, Paperclip-Freigabe ggf. separat |
| P1 | [6-h-Scheduler-Monitor](03_SIX_HOUR_MONITOR_CTO.md) | VUT-329 Engineering Operations | Draft [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30), **beide CIs rot**, Fix in vorhandenem Task |
| QA | [Top-10-Quellenprüfung](02_TOP10_QA_CHIEF_OF_STAFF.md) | VUT-332 Chief of Staff | **Done:** 5 Evidenzmängel, 4 unverifizierbar, 1 materiell stimmig (nur 10er-Sample) |
| Danach | [Ranking-ID-Integrität](04_RANKING_ID_INTEGRITY_CTO.md) | CTO, separater Task nach Abgleich bestehender Tasks | Noch nicht als neuer Task ausführen, bevor laufende Arbeiten sauber zugeordnet |
| Pausiert | [Mesabi Metallics](05_MESABI_PAUSED_CTO.md) | CTO | Quellenwachstum bis Quality-Gate aufschieben |

## Neue Aufgaben in Paperclip

**Nur wenn eine Aufgabe wirklich noch nicht existiert:** Paperclip → VuTruLabs → Tasks → New Task. Jede eigenständige Task-Datei enthält vier einzeln kopierbare Felder `Title`, `Assignee`, `Project`, `Prompt`. Alte `docs/COPILOT_*.md` sind Archiv und kein aktiver Auftrag.

**Bestehende Aufgaben nicht duplizieren.** Änderungen nur in isoliertem Branch/Task. Kein autonomer Merge/Hostinger-Deploy, keine Bewerber-Privatdaten, keine Produktionsveröffentlichung. CI-Abnahme und Hostinger-Betriebsabnahme sind unabhängig.

[Verbindliches Schema](../PAPERCLIP_TASK_FORMAT.md) · [Ursprünglicher CEO-Audit](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

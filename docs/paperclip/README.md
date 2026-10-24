# Job Tracker – Paperclip-Agenten-Aufträge

> **STAND 24.10.2026:** Paperclip [VUT-345] und unabhängige [VUT-347] bestätigen die finale RFA-Nachbesserung als **QA PASS** auf [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29), SHA `6af2058`. [Industrial CI PASS](https://github.com/hailbagel/job-tracker-public/actions/runs/39959242638), [Hostinger CI PASS](https://github.com/hailbagel/job-tracker-public/actions/runs/39959241886). **PR #29 wurde auf Ready for review umgestellt**, noch **nicht gemergt**. Fünf historische Codex-Threads sind noch offen zu reconciliieren; [Abnahme-/Limitations-Kommentar](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6381219564). [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30) ist ebenfalls **unmerged**, beide Ubuntu-CIs PASS auf `9238944`. **Keine neue Builder-Aufgabe. Kein Hostinger-Deployment.**

> **Historisch (23.10.):** Der unten erwähnte Task 08 wurde inzwischen als VUT-345 umgesetzt und unabhängig als VUT-347 abgenommen; **nicht erneut erstellen**.

> **Historisch – VUT-341:** [Task 07](07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md) ist umgesetzt und unabhängig durch VUT-344 überprüft, **nicht erneut starten**.

> **Historisch – VUT-335:** [Task 06](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md) ist umgesetzt, beide PR30-CIs sind erfolgreich. **Nicht erneut starten**.

> **Historischer Stand:** Die frühere VUT-329-Revise-Schleife wurde gelöst; die unten dokumentierten Altstände sind überholt. Aktuelle Freigabekriterien stehen oben.

## Bestehende Tasks und Reihenfolge

| Priorität | Paperclip-Auftrag | Zuständigkeit | Tatsächlicher Stand |
|---|---|---|---|
| P0 | [RFA PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) | VUT-341/344/345/347 Done | **Ready for review, 2/2 CIs PASS; noch nicht gemergt; fünf alte Review-Threads reconciliieren** |
| P1 | [6-h-Monitor PR #30](https://github.com/hailbagel/job-tracker-public/pull/30) | VUT-329/335 Done | **2/2 CIs PASS auf Head `9238944`; noch nicht gemergt, nach PR #29 neue Integration/CI** |
| QA | [Top-10-Quellenprüfung](02_TOP10_QA_CHIEF_OF_STAFF.md) | VUT-332 Chief of Staff | **Done:** 5 Evidenzmängel, 4 unverifizierbar, 1 materiell stimmig (nur 10er-Sample) |
| Danach | [Ranking-ID-Integrität](04_RANKING_ID_INTEGRITY_CTO.md) | CTO, separater Task nach Abgleich bestehender Tasks | Noch nicht als neuer Task ausführen, bevor laufende Arbeiten sauber zugeordnet |
| Pausiert | [Mesabi Metallics](05_MESABI_PAUSED_CTO.md) | CTO | Quellenwachstum bis Quality-Gate aufschieben |

## Bereits erledigter Agentenauftrag

**[VUT-335 – Scheduler P1 Follow-up](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md)** wurde in Paperclip erstellt und vom Builder am 22.10. als DONE gemeldet. **Nicht erneut erstellen oder kopieren.** Der weitere Gate ist unabhängiger Code-Review / finale CI, dann getrennte Freigabe beider PRs.

## Historisch: Task 08 abgeschlossen

[Task 08](08_RFA_FINAL_RELEASE_GATE_BUILDER.md) wurde als **VUT-345** umgesetzt und durch **VUT-347** unabhängig geprüft (PASS). **Nicht erneut erstellen.** Aktueller nächster Schritt ist Review-Thread-Reconciliation und kontrollierte PR-Integration; kein neuer Builder-Auftrag.

## Neue Aufgaben in Paperclip

**Nur wenn eine Aufgabe wirklich noch nicht existiert:** Paperclip → VuTruLabs → Tasks → New Task. Jede eigenständige Task-Datei enthält vier einzeln kopierbare Felder `Title`, `Assignee`, `Project`, `Prompt`. Alte `docs/COPILOT_*.md` sind Archiv und kein aktiver Auftrag.

**Bestehende Aufgaben nicht duplizieren.** Änderungen nur in isoliertem Branch/Task. Kein autonomer Merge/Hostinger-Deploy, keine Bewerber-Privatdaten, keine Produktionsveröffentlichung. CI-Abnahme und Hostinger-Betriebsabnahme sind unabhängig.

[Verbindliches Schema](../PAPERCLIP_TASK_FORMAT.md) · [Ursprünglicher CEO-Audit](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

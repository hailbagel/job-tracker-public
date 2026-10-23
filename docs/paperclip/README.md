# Job Tracker – Paperclip-Agenten-Aufträge

> **AKTUELL – 23.10.2026, 14:41 Berlin:** Paperclip **VUT-341** und unabhängige **VUT-344** (RFA mandatory/preferred) erfolgreich; [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) Head `29b03a3`, beide Ubuntu CI grün ([Industrial](https://github.com/hailbagel/job-tracker-public/actions/runs/39954763521), [Hostinger](https://github.com/hailbagel/job-tracker-public/actions/runs/39954763376)). **Noch nicht mergen:** früherer Codex-Review enthält drei P1-Risiken, die im aktuellen Code fortbestehen: Degree-Fachrichtung, Arbeitserlaubnis-Land, Ranking-Cache. [Belege](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6365211451). **[GENAU EIN weiterer Paperclip-Folgeauftrag (vier Copy-Boxen)](08_RFA_FINAL_RELEASE_GATE_BUILDER.md)**. PR #30 Head `9238944` hat nun beide Linux-CIs grün, ist noch ungemergt. Kein Hostinger-Deploy.

> **Historisch – VUT-341:** [Task 07](07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md) ist umgesetzt und unabhängig durch VUT-344 überprüft, **nicht erneut starten**.

> **Historisch – VUT-335:** [Task 06](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md) ist umgesetzt, beide PR30-CIs sind erfolgreich. **Nicht erneut starten**.

> **Historischer Stand:** Die frühere VUT-329-Revise-Schleife wurde gelöst; die unten dokumentierten Altstände sind überholt. Aktuelle Freigabekriterien stehen oben.

## Bestehende Tasks und Reihenfolge

| Priorität | Paperclip-Auftrag | Zuständigkeit | Tatsächlicher Stand |
|---|---|---|---|
| P0 | [RFA PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) | VUT-341 + VUT-344 Done | **2/2 CI grün; drei weitere P1 Review-Gates offen; Task 08** |
| P1 | [6-h-Monitor PR #30](https://github.com/hailbagel/job-tracker-public/pull/30) | VUT-329 + VUT-335 Done | **2/2 CI grün; nicht gemergt; erst nach PR #29 auf main synchronisieren** |
| QA | [Top-10-Quellenprüfung](02_TOP10_QA_CHIEF_OF_STAFF.md) | VUT-332 Chief of Staff | **Done:** 5 Evidenzmängel, 4 unverifizierbar, 1 materiell stimmig (nur 10er-Sample) |
| Danach | [Ranking-ID-Integrität](04_RANKING_ID_INTEGRITY_CTO.md) | CTO, separater Task nach Abgleich bestehender Tasks | Noch nicht als neuer Task ausführen, bevor laufende Arbeiten sauber zugeordnet |
| Pausiert | [Mesabi Metallics](05_MESABI_PAUSED_CTO.md) | CTO | Quellenwachstum bis Quality-Gate aufschieben |

## Bereits erledigter Agentenauftrag

**[VUT-335 – Scheduler P1 Follow-up](06_SCHEDULER_P1_FOLLOWUP_BUILDER.md)** wurde in Paperclip erstellt und vom Builder am 22.10. als DONE gemeldet. **Nicht erneut erstellen oder kopieren.** Der weitere Gate ist unabhängiger Code-Review / finale CI, dann getrennte Freigabe beider PRs.

## PR #29 – letzter konkreter Release-Gate-Folgeauftrag

**[Task 08 – Fachrichtung / Arbeitserlaubnis / Cache](08_RFA_FINAL_RELEASE_GATE_BUILDER.md)**: Noch nicht als Paperclip Task erstellt, vier Copy-Boxen zum Übernehmen. [Task 07](07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md) wurde von VUT-341 umgesetzt; VUT-344 bestätigte QA. Keine Duplikate und kein neuer GitHub-PR.

## Neue Aufgaben in Paperclip

**Nur wenn eine Aufgabe wirklich noch nicht existiert:** Paperclip → VuTruLabs → Tasks → New Task. Jede eigenständige Task-Datei enthält vier einzeln kopierbare Felder `Title`, `Assignee`, `Project`, `Prompt`. Alte `docs/COPILOT_*.md` sind Archiv und kein aktiver Auftrag.

**Bestehende Aufgaben nicht duplizieren.** Änderungen nur in isoliertem Branch/Task. Kein autonomer Merge/Hostinger-Deploy, keine Bewerber-Privatdaten, keine Produktionsveröffentlichung. CI-Abnahme und Hostinger-Betriebsabnahme sind unabhängig.

[Verbindliches Schema](../PAPERCLIP_TASK_FORMAT.md) · [Ursprünglicher CEO-Audit](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

# Job Tracker – Paperclip-Agenten-Aufträge

> **Aktuell 22.10.2026 – VUT-329 / Draft PR #30:** **REVISE statt ACCEPT**. Beide GitHub-Actions-CIs sind rot wegen unverändertem `tests/test_publication.py`-Altfehler. [**Revise-Kommentar zum Kopieren**](VUT329_PR30_REVISE.md). Keine neue Aufgabe, kein Merge/Deploy.

> **LIVE-STATUS, 22.10.2026:** Der RFA-Task ist **bereits angelegt** (Paperclip **VUT-328**, Builder). Die parallele CTO-Koordination **VUT-331** ist abhängig/blockiert. Top-10-QA **VUT-332** ist erledigt. **Keine dieser drei Aufgaben neu erstellen.** Aktueller nächster Schritt: [bestehenden VUT-328 / PR #29 sicher wiederaufnehmen](VUT328_PR29_RECOVERY.md). Der frühere Vorschlag „Jetzt starten“ unten ist nur das ursprüngliche Task-Template, kein Live-Status.


**Diese Seite ist der einzige aktive Einstiegspunkt für neue Paperclip-Aufträge.** Keine VS-Copilot-Chats und keine lokalen VS-Code-Workspaces nötig. **Jede Datei hat vier getrennte Kopierboxen für Title, Assignee, Project und Prompt.**

| Reihenfolge | Paperclip-Auftrag | Agent | Status |
|---|---|---|---|
| **1** | [RFA-Pflichtanforderungen / falsches GREEN](01_RFA_REQUIREMENTS_CTO.md) | Builder: VUT-328 / CTO: VUT-331 | **BLOCKIERT – PR #29 CI**, keine neue Aufgabe |
| **2** | [10 Top-Ranking-Stellen gegen Original prüfen](02_TOP10_QA_CHIEF_OF_STAFF.md) | Chief of Staff: VUT-332 | **DONE** – fünf Abweichungen, vier unverifizierbar, ein passender Datensatz (zehn geprüft) |
| 3 | [6-h-Scheduler-Monitor korrigieren](03_SIX_HOUR_MONITOR_CTO.md) | Engineering Operations: VUT-329 | **IN REVIEW – PR #30 CI rot; bestehende Confirmation revidieren** |
| 4 | [Ranking-IDs exakt mit aktuellen Quellen abgleichen](04_RANKING_ID_INTEGRITY_CTO.md) | CTO | Nach 1 und 3 |
| 5 | [Mesabi/JazzHR-Codeadapter](05_MESABI_PAUSED_CTO.md) | CTO | **Pausiert** |

## Einfügen

1. **Paperclip → VuTruLabs → Tasks → New Task**.
2. Aufgabe verlinkt oben öffnen. Per Kopiersymbol **Title** → Task-Titel, **Assignee** → Agent, **Project** → Projekt, **Prompt** → Beschreibung. Vier getrennte Felder.
3. Task in Paperclip starten. **GitHub-Vorlage allein legt den Task nicht an.** Ergebnisse/CI/PRs in Paperclip/GitHub nachweisen. Wenn Agent Rechte nicht hat, `BLOCKED` melden.

**Regeln:** Nur eine codierende Instanz je Checkout/Branch, read-only Chief of Staff darf parallel. Keine parallele Copilot-Arbeit, kein automatischer Merge, Hostinger-Eingriff oder Produktiv-Datenimport. Private Kandidatendaten nie ins Repo. Bestehende Tasks nicht duplizieren; VUT-318 war falsch zugeordnet; VUT-319 ist bereits erledigte Mesabi-Feasibility.

**Archive:** Alte `docs/COPILOT_*.md` und `docs/COPY_*_COPILOT_*.md` sind historische VS-Copilot-Prompts und keine aktiven Paperclip-Aufträge. [Task-Schema](../PAPERCLIP_TASK_FORMAT.md) · [Audit-Herkunft](../PAPERCLIP_JOB_TRACKER_QUALITY_REMEDIATION_2026-10-22.md).

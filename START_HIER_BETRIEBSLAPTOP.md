# START HIER – Job Tracker / VuTruLabs

**Arbeitsmodus ab 22.10.2026: Paperclip-Agenten bevorzugt.** Keine doppelte Entwicklung durch Copilot und Paperclip fuer dieselbe Aufgabe.

## 1. Paperclip-Auftraege – immer exakt vier Kopierbloecke

**[VERBINDLICHES TASK-FORMAT: Title / Assignee / Project / Prompt](docs/PAPERCLIP_TASK_FORMAT.md)**

**WO EINFUEGEN:** Paperclip → VuTruLabs → Tasks → New Task; **jeden der vier separat dargestellten Plain-text-Blocks einzeln** in das passende Eingabefeld kopieren. Nicht den ganzen GitHub-Artikel oder einen zusammenhaengenden Prompt kopieren. Die separate Projektauswahl und der Agent sind im Task klar benannt.

**Aktuell primaerer Entwicklungsauftrag:** [**PAPERCLIP – Mesabi Metallics JazzHR CTO Adapter**](docs/PAPERCLIP_MESABI_AGENT_IMPLEMENTATION.md) (GitHub [Issue #26](https://github.com/hailbagel/job-tracker-public/issues/26), Grundlage Paperclip VUT-319). CTO kann Code, Tests, Branch und Draft-PR erstellen. Kein Merge, kein Hostinger-Deploy und keine Produktionsaktivierung.

**Historische, bereits bearbeitete Paperclip-Tasks:** [VUT-317 bis VUT-320 – vier jeweils separat kopierbare Felder](docs/PAPERCLIP_JOB_TRACKER_TASKS_2026-10-21.md). **Nicht erneut anlegen.** VUT-318 ist laut Owner falsch zugeordnet und wird ignoriert; VUT-319 hat die Machbarkeitsstudie abgeschlossen.

**Wichtig:** Repo-Prompt-Dateien auf GitHub sind Vorlagen, keine in Paperclip erstellten Tasks. Auch ein Paperclip-`Done` ersetzt keine Auswertung der tatsächlichen CI-/PR-Evidenz.

## 2. GitHub und Freigaben

- [PR #23](https://github.com/hailbagel/job-tracker-public/pull/23) und [PR #25](https://github.com/hailbagel/job-tracker-public/pull/25) wurden gemergt. SMS group ist damit **nicht automatisch aktiv**.
- [Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24): Ranking-IDs/Datenqualitaet, unabhaengig vom Mesabi-Adapter.
- [Issue #26](https://github.com/hailbagel/job-tracker-public/issues/26): Mesabi/JazzHR-Adapter; nach Paperclip CTO Draft-PR pruefen.
- Hostinger-Produktivzustand laesst sich nicht allein durch GitHub belegen; ohne gesonderte Pruefung/Freigabe keine Scheduler-, Systemd-, Hostinger- oder Publisher-Aenderungen.

## 3. Nur wenn bewusst lokal in VS Code gearbeitet wird

**VS Code → File → New Window → File → Open Folder → `C:\Users\minkusp\Projects\job-tracker-public`.** Nicht im `ESP32-Paxcounter_22 (Workspace)` oder im `copilot-chat-exporter`-Workspace weiterentwickeln.

[**KOPIEREN 01 – sichere PowerShell Git-Synchronisierung**](docs/COPY_01_VSCODE_POWERSHELL_SYNC.md). Nur bei sauberem Arbeitsbaum Fast-Forward-Pull. Keine lokalen Dateien einfach resetten, bereinigen oder ueberschreiben. `copilot-chat-exporter` mit privaten lokalen Backup-Daten bleibt separat.

**Copilot-Fallbacks, derzeit nicht parallel starten:** [COPY_05 SMS](docs/COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md), [COPY_06 Issue #24](docs/COPY_06_COPILOT_ISSUE24_RANKING_INTEGRITY.md), [COPY_07 Mesabi](docs/COPY_07_COPILOT_MESABI_JAZZHR_ADAPTER.md). Besonders COPY_07 ist **pausiert**, solange Paperclip CTO fuer Mesabi verantwortlich ist.

## Regel fuer neue Agentenauftraege

1. Paperclip-Task mit **vier GitHub-Kopierbloecken** (`Title`, `Assignee`, `Project`, `Prompt`) erstellen.
2. Agent prueft bei Taskstart Repository, gesicherten Workspace und Schreibberechtigungen. Bei Blockern `BLOCKED` statt `Done`.
3. Tests/CI nachweisen, einen separaten Draft-PR erstellen und Link/Commit im Paperclip-Task hinterlegen.
4. Merge und Produktion nur nach separater Abnahme. Ein Task ist erst mit nachvollziehbarem Ergebnis erfolgreich.

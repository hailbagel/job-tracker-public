# VERBINDLICHES PAPERCLIP-TASK-FORMAT – VuTruLabs

> Für neue Aufgaben nur [docs/paperclip/](paperclip/README.md) verwenden: eine Task-Datei, **vier Copy-Boxen**, Paperclip-Agent als Ausführung. Kein VS Copilot.

**Regel fuer alle neuen Paperclip-Auftraege:** Jeder Task wird auf GitHub mit exakt **vier separaten Plain-text-Kopierbloecken** vorbereitet, in dieser Reihenfolge: **Title**, **Assignee**, **Project**, **Prompt**. Keine entscheidenden Eingabewerte nur als Markdown-Inline-Text oder in einem grossen Sammelblock verstecken.

**WO EINFUEGEN:** Paperclip → VuTruLabs → Tasks → New Task. Jeder Block wird **einzeln** per Kopiersymbol aus GitHub in sein entsprechendes Feld kopiert.

## Muster

### Title
```text
JT-EXAMPLE – One outcome-driven task
```

### Assignee
```text
CTO
```

### Project
```text
Job Tracker Public
```

### Prompt
```text
Task: JT-EXAMPLE – deliver a verifiable outcome.

Repository: https://github.com/hailbagel/job-tracker-public
Scope: Explicitly describe exactly which result is required.
Access: Inspect available capabilities first; report BLOCKED if missing.
Execution: Work on a dedicated, clean branch; do not overwrite or delete unrelated files.
Validation: Run the relevant tests and report actual evidence.
Delivery: Provide commit SHA, PR link, test results, blockers, and next approval gate.
Safety: No Hostinger change, deployment, production publication, private-data export or merge without separate approval.
```

**Nur eine Vorlage:** In konkreten Aufgaben den Beispieltext vollstaendig ersetzen; nicht den Beispiel-Task starten.

## Verbindliche Qualitaetskriterien

- **Title:** Eine konkrete, kurze Aufgabe statt eines Projekt-/Chat-Namens.
- **Assignee:** Exakter Agentenname in Paperclip, z. B. `CTO` oder `Chief of Staff`. Nicht mehrere Alternativen in einen einzigen Copyblock schreiben.
- **Project:** Exakter Paperclip-Projektname, z. B. `Job Tracker Public`.
- **Prompt:** Eigenstaendig verstaendlich. Enthaelt Referenzen, Berechtigungen, erwartete Artefakte, Tests, Definition of Done, Verbote und Berichtspflicht.
- **Ein Task = ein Ergebnis.** Bestehende Done-Tasks nicht erneut anlegen. Keine naiven Subtask-Kaskaden, kein doppelter Copilot-/Paperclip-Code-Auftrag.
- **Paperclip-Status ist nicht GitHub-Status.** Repo-Datei schreiben bedeutet nicht, dass in der Paperclip-Instanz ein Task angelegt oder ausgefuehrt wurde.
- **Read-only Review und Coding strikt trennen:** Reviews duerfen nichts mergen; Coding-Agenten duerfen ohne Freigabe nicht produktiv deployen.
- **Belege statt Behauptungen:** Task-Abschluss benoetigt Links/Commit-IDs/Test-Logs bzw. `BLOCKED`, falls Zugang oder vollstaendige Evidenz fehlt.

**Bei mehreren Paperclip-Auftraegen:** Jeder Auftrag bekommt seine eigenen vier Kopierbloecke unmittelbar beieinander. Eine indexierte Uebersicht darf den eigentlichen Copyblock nicht ersetzen.

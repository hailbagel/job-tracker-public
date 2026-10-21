# START HIER — Job Tracker auf Betriebslaptop / VS Code

**Ziel:** Die Entwicklung an `hailbagel/job-tracker-public` nahtlos auf dem Betriebslaptop fortsetzen, ohne den funktionierenden Hostinger-Produktivbetrieb anzufassen.

## Reihenfolge: nur ZWEI Kopieraktionen

| Schritt | GitHub-Datei | Wofür? | WO genau einfügen? |
|---|---|---|---|
| **1 — zuerst** | [COPY_01_VSCODE_POWERSHELL_SYNC.md](docs/COPY_01_VSCODE_POWERSHELL_SYNC.md) | Richtige GitHub-Repo prüfen und aktuellen `main` per sicherem Fast-Forward auf den Betriebslaptop holen | **VS Code → bestehendes Projekt `job-tracker-public` öffnen → Terminal → New Terminal → PowerShell.** Dort ausschließlich den PowerShell-Codeblock der Datei kopieren und ausführen. |
| **2 — danach** | [COPY_02_COPILOT_INDUSTRIAL_AGENT.md](docs/COPY_02_COPILOT_INDUSTRIAL_AGENT.md) | Copilot anweisen, vier Industriequellen zu prüfen und zunächst eine saubere SMS-group-Automatisierung auf neuem Feature-Branch zu entwickeln | **VS Code → Copilot Chat → Agent → New Chat.** Dort ausschließlich den `text`-Codeblock der Datei hineinkopieren und absenden. **Nicht in PowerShell.** |

**Wichtig:** Beide Dateien wurden auf GitHub `main` gespeichert; Du musst die Textbefehle nicht selbst in Dateien anlegen. Eine Änderung von `main` durch den Hostinger-Publisher (neue öffentliche Datensätze) ist normal und wird beim Pull berücksichtigt.

## Wenn Schritt 1 bei `?? patrick.json` stoppt

Das ist ein lokales privates Profil, **kein Fehler von GitHub**. Keine Datei löschen, committen oder pushen. Die geprüfte Einmal-Reparatur steht hier:

**[COPY_01A — patrick.json in den lokalen ignorierten Privatordner verschieben](docs/COPY_01A_PRIVATE_PATRICK_JSON_FIX.md)**

**WO einfügen:** VS Code → Terminal → PowerShell, **nicht** Copilot/Hostinger. Der Code verschiebt die lokale Datei nur nach `configs/private_profiles/patrick.json`, wenn genau diese eine unversionierte Datei existiert, keine anderen Änderungen vorliegen, der Zielpfad frei und durch `.gitignore` geschützt ist. Danach nochmals **Schritt 1**, dann Schritt 2 ausführen.

## Erwartete Rückmeldungen

- Nach Schritt 1: `=== WORK LAPTOP REPOSITORY READY ===`, danach `main...origin/main` und ein Commit-Hash.
- Nach Schritt 2: Copilot soll `docs/COPILOT_INDUSTRIAL_WORK_LAPTOP_HANDOFF_2026-10-21.md` sowie `docs/COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md` lesen, die vier Quellen untersuchen und für die erste implementierbare Quelle **einen DRAFT PR** mit Code, Tests und nachgewiesener Quelle pushen.

## Keine Aktionen auf Hostinger

Hostinger läuft unabhängig weiter mit stündlicher Scheduler-Prüfung und einer vorläufigen **6-Stunden-Mindestfrist** zwischen erfolgreichen Datenveröffentlichungen. Die neueste hier dokumentierte Abnahme vom 21.10.2026 zeigte `0 failures / 2 warnings`. Die zwei bekannten Warnungen gehören zu den gesperrten/fehlerhaften Tesla- und Jacobs-Quellen.

**Keinen zweiten Repository-Clone über vorhandene Dateien anlegen, kein `git reset --hard`, `git clean`, Force-Push oder Copilot-Auto-Merge.** Bei `STOP` in Schritt 1 zuerst den Ausgangszustand prüfen, statt Daten zu überschreiben.

## Fachlicher Kontext (zum Nachlesen, nicht vollständig ins Chat-Feld kopieren)

- [Copilot Work-Laptop Handoff](docs/COPILOT_INDUSTRIAL_WORK_LAPTOP_HANDOFF_2026-10-21.md)
- [Industrial Employers – Originaltask](docs/COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md)
- [Produktions- und Veröffentlichungsvertrag](docs/public_data_publication.md)

Der nächste Entwicklerauftrag ist unabhängig vom bisherigen Hostinger-Scheduler: **SMS group → Midrex → Mesabi Metallics → Siemens AG**. Jede Quelle benötigt verifizierte öffentliche Erfassung, vollständige Seitenabdeckung, Tests und eine separate Freigabe vor Produktivschaltung.

## Nächster Meilenstein — SMS group (PR #23)

Die SMS-group-d.vinci-Implementierung liegt im [Draft PR #23](https://github.com/hailbagel/job-tracker-public/pull/23), Linux-CI ist erfolgreich. Der PR aktiviert noch keine produktive SMS-Erfassung und darf nur nach ausdrücklicher Freigabe gemergt werden.

**Nach Merge von PR #23:** [KOPIEREN 04 — Copilot-Produktivvorbereitung](docs/COPY_04_COPILOT_SMS_PRODUCTION_READINESS.md) im **bestehenden VS-Code-Copilot-Agent-Chat** (nicht Terminal) einfügen. Dadurch wird der nächste, separat geprüfte PR für Bootstrap/Publisher/Audit und sichere Aktivierung vorbereitet. **Nicht** eigenständig deployen oder Timer ändern.

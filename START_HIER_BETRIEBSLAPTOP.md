# START HIER – Job Tracker auf dem Betriebslaptop

**Aktueller Stand: 21.10.2026.** Diese Anleitung ersetzt die fruehere Reihenfolge fuer PR #23 und PR #25. Beide Pull Requests sind bereits gemergt. Der alte VS-Code-Copilot-Chat `Industrial Job Coverage` ist in der aktuellen Workspace-Ansicht nicht erreichbar; kein Grund, die Arbeit anzuhalten.

## 1. Richtigen VS-Code-Workspace oeffnen

**VS Code → File → New Window → File → Open Folder → `C:\Users\minkusp\Projects\job-tracker-public`.**

**Nur diesen einen Projektordner oeffnen.** Nicht `ESP32-Paxcounter_22 (Workspace)`, nicht `copilot-chat-exporter`, nicht einen `Untitled (Workspace)` mit mehreren Projekten. Andere Projekte bleiben in ihren eigenen Ordnern/Fenstern erhalten. Keine alten Chats oder Arbeitsbereiche loeschen.

## 2. Lokal sicher mit GitHub synchronisieren

[**KOPIEREN 01 – VS-Code-PowerShell-Synchronisierung**](docs/COPY_01_VSCODE_POWERSHELL_SYNC.md).

**WO EINFUEGEN:** Im neuen Job-Tracker-Fenster → **Terminal → New Terminal → PowerShell**. Den kompletten PowerShell-Block aus COPY_01 kopieren. Er prueft Repository und lokale Aenderungen und fuehrt nur bei sauberem Arbeitsbaum einen Fast-Forward-Pull von `main` aus. Bei `STOP` nicht resetten, nicht cleanen, nichts staschen oder ueberschreiben; Status pruefen.

## 3. Neuen Copilot-Agent-Chat verwenden

Im **gleichen separaten Job-Tracker-Fenster** rechts **Copilot → Agent → New Chat**. Neuer Sitzungsname: **`Job Tracker – Development`**. Die fruehere Sitzung wird fuer die weiteren Arbeiten nicht gebraucht; die Referenz ist das aktuelle GitHub-Repository.

**JETZT NAeCHSTER ENTWICKLUNGSAUFTRAG:**

[**KOPIEREN 05 – SMS-Hostinger-Runbook mit sicherem Preflight, Opt-in und Rollback vorbereiten**](docs/COPY_05_COPILOT_SMS_HOSTINGER_ROLLOUT_REVIEW.md).

**WO EINFUEGEN:** Den kompletten `text`-Block **in den neuen Copilot-Agent-Chat**. **NICHT ins Terminal und NICHT auf Hostinger.** Copilot soll Dokumentation, Tests und einen getrennten PR vorbereiten. Kein Merge oder Hostinger-Deploy ohne nachpruefbare Abnahme. Der SMS-Adapter ist durch `JOB_TRACKER_ENABLE_SMS_GROUP` standardmaessig deaktiviert.

**ANSCHLIESSEND, als separates Arbeitspaket:**

[**KOPIEREN 06 – Issue #24: Ranking-IDs gegen aktuelle Quelldaten pruefen**](docs/COPY_06_COPILOT_ISSUE24_RANKING_INTEGRITY.md).

**WO EINFUEGEN:** In den Job-Tracker-Copilot-Agent-Chat, nachdem COPY_05 erledigt oder bewusst pausiert wurde. Separater Branch/PR. Keine Aenderung an der Produktiv-Pipeline oder an privaten Profilen.

## Verifizierter GitHub-Status zum Zeitpunkt dieser Anleitung

- [PR #23](https://github.com/hailbagel/job-tracker-public/pull/23): Basis fuer SMS d.vinci, bereits gemergt.
- [PR #25](https://github.com/hailbagel/job-tracker-public/pull/25): SMS mit default-off produktionsseitigem Opt-in vorbereitet und gemergt; **SMS ist dadurch NICHT automatisch live**.
- [Issue #24](https://github.com/hailbagel/job-tracker-public/issues/24): noch offen, betrifft Ranking-ID-Datenqualitaet.
- Die GitHub-Abfrage am 21.10.2026 zeigte **keinen offenen Pull Request**.
- Hostinger-Produktivzustand und Live-SMS-Erfassung koennen nicht allein durch den GitHub-Stand verifiziert werden. Ohne extra Freigabe weder Systemd-Scheduler noch Umgebungsvariablen auf Hostinger veraendern.

## Grundregel

**Arbeitsbereiche strikt trennen, aber alle Aufgaben und Copilot-Prompts versioniert im passenden Repository halten.** Kein zusaetzlicher Clone in einen vorhandenen Projektordner; keine lokalen unversionierten Daten in GitHub pushen. `copilot-chat-exporter` und dessen lokale Chat-Backups bleiben eigenstaendig und unberuehrt.

Aeltere Dateien `COPY_02_COPILOT_INDUSTRIAL_AGENT.md` und `COPY_04_COPILOT_SMS_PRODUCTION_READINESS.md` sind historischer Kontext; nicht nochmals als neue Aufgaben ausfuehren.

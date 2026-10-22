# START HIER – Job Tracker / Paperclip

> **Neuster verifizierter Stand: 22.10.2026.** VUT-335 ist in Paperclip DONE; der Builder hat beide P1 False-OK-Korrekturen in [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30), Commit `9238944d4770ac95976e304af996ee2d54be8ec7`, gepusht. Der Hostinger-Scheduler-Testworkflow ist grün; der andere Linux-Testjob ist erfolgreich, während der Gesamtworkflow zuletzt noch als `in_progress` angezeigt wurde. Der **neue Codex-Review für PR #30 läuft**. Keine neue Implementierungs-Aufgabe starten.

## Jetzt Review-Gates prüfen

1. **[PR #29 – RFA Gate](https://github.com/hailbagel/job-tracker-public/pull/29):** Draft, 2/2 Linux CI grün; [unabhängige Codex-Prüfung angefragt](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6349413953), Ergebnisse erst bewerten.
2. **[PR #30 – Scheduler-Monitor](https://github.com/hailbagel/job-tracker-public/pull/30):** P1-Korrekturen durch VUT-335 fertig; [CI prüfen](https://github.com/hailbagel/job-tracker-public/actions/runs/39837694307) und [laufenden Codex-Review](https://github.com/hailbagel/job-tracker-public/pull/30) abnehmen. Offen gebliebene Findings müssen vor Merge geklärt sein.
3. **Merge-Freigabe:** Nur bei akzeptiertem unabhängigen Review und grünen vollen GitHub CI; PR #29 vor PR #30; nach Merge von PR #29 Branch von PR #30 aktualisieren und CI für neue Integration erneut prüfen. Keine automatische Produktion.
4. **Hostinger separat:** Installierte Revision, dauerhafter Zustand und drei planmäßige erfolgreiche 6-h-Läufe nachweisen. Code-Tests allein sind keine Host-Abnahme.
5. Danach [Ranking-ID-Audit #24](https://github.com/hailbagel/job-tracker-public/issues/24). Quellen-Onboarding bleibt vorerst zurückgestellt.

[**Paperclip-Taskindex**](docs/paperclip/README.md). Bestehende VUT-328/329/331/332/335-Tasks nicht duplizieren. Neue Tasks nur mit vier separaten kopierbaren Feldern (`Title`, `Assignee`, `Project`, `Prompt`). Historische VS-Copilot-Prompts bleiben Archiv.

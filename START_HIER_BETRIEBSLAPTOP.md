# START HIER – Job Tracker / Paperclip

> **JETZT: VUT-329 per Nachricht an Engineering Operations reparieren lassen. Nicht erneut Review anfordern!**

**[KOPIERFERTIGE ANWEISUNG – VUT-329 / PR #30](docs/paperclip/VUT329_PR30_REVISE.md)**

Die vorherige `Revise`-Auswahl wurde als abgelehnte Bestätigung ohne Änderungsauftrag verarbeitet; laut Screenshot ist VUT-329 zur sofortigen Bearbeitung an Engineering Operations zurückgegangen. Daher **im bestehenden Task** die technische Anweisung senden. Nicht `New Task`, nicht erneut `Revise`.

- [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29): RFA-Fix, **grüne CI**, noch Draft.
- [PR #30](https://github.com/hailbagel/job-tracker-public/pull/30): 6-h-Monitor, **zwei rote CIs**, noch Draft. Uralte SMS-PR-Dateilistenassertion in `tests/test_publication.py` ist der eine relevante Testblocker.
- VUT-332: unabhängige Top-10-QA **Done**; kein zusätzlicher Task.
- Weitere Tasks und Vorlagen: [Paperclip-Index](docs/paperclip/README.md).

**Arbeitsprinzip:** Paperclip-Agenten bearbeiten bestehende Tasks, berichten CI-/PR-Evidenz. Neue Tasks erhalten vier getrennte Copy-Boxen (`Title`, `Assignee`, `Project`, `Prompt`). Alte Copilot-Prompts sind Archiv. Kein Merge, keine Hostinger-Änderung, keine Produktion ohne separate Freigabe.

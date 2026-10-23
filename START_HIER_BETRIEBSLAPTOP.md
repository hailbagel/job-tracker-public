# START HIER – Job Tracker / Paperclip

> **Stand 23.10.2026, ca. 14:41 Berlin:** [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) bleibt Draft/ungemergt; Code-Fixes VUT-341 und unabhängige QA VUT-344 Done, zwei Ubuntu-CIs grün auf SHA `29b03a3`. Drei wesentliche Review-Gates sind im aktuellen Code noch offen: Degree-Fachrichtung, Work-Authorization-Land, Cache-Version. [Evidenz im PR](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6365211451).

## JETZT in Paperclip
**[Task 08: Vier Copy-Boxen, vorhandenen PR #29 abschließen](docs/paperclip/08_RFA_FINAL_RELEASE_GATE_BUILDER.md)**. Eine neue, eng begrenzte Builder-Aufgabe; **kein neuer GitHub-PR**. Task 07/VUT-341 bereits Done, **nicht wiederholen**. Keine andere parallele Branch-Bearbeitung.

## Zweiter PR
[PR #30 – 6-Stunden-Scheduler](https://github.com/hailbagel/job-tracker-public/pull/30) Head `9238944`, beide Ubuntu-CIs mittlerweile grün. PR bleibt ungemergt. **Erst PR #29 Qualität/Review/Merge, dann PR #30 Branch aktualisieren, erneut CI+Code-Review und gesonderte Mergefreigabe.**

## Produktionsabnahme
**Kein Hostinger-Deployment jetzt:** Betriebsversion + Journale, persistenter Zustand und drei voneinander unabhängige erfolgreiche geplante 6-h-Läufe müssen später nachgewiesen werden.

[Zentraler Paperclip-Index](docs/paperclip/README.md). Alte Copilot-Prompts bleiben Archiv. Neue Paperclip Tasks immer mit vier separat kopierbaren Feldern.

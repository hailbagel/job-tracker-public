# START HIER – Job Tracker / Paperclip

> **Aktuelle Blockade, 22.10.2026:** Eigenständige Inspektion von [PR #29](https://github.com/hailbagel/job-tracker-public/pull/29) ergab **zwei ungetestete Pflichtanforderungs-Randfälle**. [Nachweise direkt als Kommentar im PR](https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6349563992). PR #29 unverändert Draft; NICHT mergen. [**Task 07 – vier Copy-Boxen für den Paperclip-Builder**](docs/paperclip/07_RFA_P1_MANDATORY_COVERAGE_BUILDER.md). Bearbeitung NUR im bestehenden PR #29.

- VUT-328/331/332 und VUT-335 sind erledigt; **nicht duplizieren**.
- PR #30 (Scheduler) Commit `9238944`, [Scheduler CI grün](https://github.com/hailbagel/job-tracker-public/actions/runs/39837694272), [Industrial Source Linux CI Gesamtlauf zum letzten Check noch in_progress](https://github.com/hailbagel/job-tracker-public/actions/runs/39837694307). Unabhängiger Review beider PRs ist noch nicht abgeschlossen.
- PR #29 hatte zwei grüne CI-Checks auf altem Kopf-Commit. Neue Randfälle benötigen neue Tests und Codeänderung; danach volle CI und unabhängigen Review.
- **Merge-Reihenfolge:** PR #29 erst nach vollständiger Abnahme, danach PR #30 synchronisieren, CI wiederholen und erst dann separat entscheiden. **Hostinger**: zusätzliche unabhängige Betriebs-/Laufzeitnachweise erforderlich (installierter Commit, persistenter State, drei geplante 6-h-Runs).

[Paperclip Task Index](docs/paperclip/README.md). Keine neue Quellenerweiterung und keine Live-Veröffentlichung bis zur Qualitätsabnahme.

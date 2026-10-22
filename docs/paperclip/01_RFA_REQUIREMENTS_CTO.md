# PAPERCLIP TASK – RFA: Pflichtanforderungen und falsches GREEN

**STATUS:** JETZT, CTO, P0. **Ziel:** Paperclip → VuTruLabs → New Task. Jeden der folgenden vier Codeblöcke **einzeln** in das zugehörige Feld kopieren. **Nicht** in VS Copilot. Noch kein Paperclip-Task durch diese Repo-Datei angelegt.

## Title
```text
JT-RFA-QUALIFICATIONS – Repair Greenhouse fields and hard gates
```

## Assignee
```text
CTO
```

## Project
```text
Job Tracker Public
```

## Prompt
```text
Role: CTO implementation agent, VuTruLabs Paperclip.
Task: JT-RFA-QUALIFICATIONS – correct the false-GREEN ranking pathway.
Repo: https://github.com/hailbagel/job-tracker-public
Issue: https://github.com/hailbagel/job-tracker-public/issues/27
Priority: P0. Do not delay this work for Mesabi or additional source adapters.

Ground truth verified 2026-10-22:
- jobtracker/acquisition.py greenhouse() sets mission=item["content"] without mapping requirements.
- Snapshot data/rocket-factory-augsburg/processed/job_details.csv contains 55 current rows, all 55 requirements blank, though mission HTML has qualifications sections.
- jobtracker/patrick.py accepts any of mission/requirements/benefits as sufficient, and analysis/profile_ranking.py uses requirements for mandatory hard gates.
- Snapshot data/patrick/processed/patrick_targets.md (2026-10-21) shows RFA 4997134101 GREEN 77, 4944174101 GREEN 73, both with "Hard gates: none".
- Public originals: https://job-boards.eu.greenhouse.io/rocketfactoryaugsburgag/jobs/4997134101 and https://job-boards.eu.greenhouse.io/rocketfactoryaugsburgag/jobs/4944174101

Implementation:
1. Inspect current origin/main, all open PRs, relevant source, existing parsers/tests and the exact Issue #27. Confirm no competing PR. Work in isolated clean workspace/feature branch feature/rfa-qualifications-gate. If checkout dirty, do not reset/stash/delete or overwrite work. Stop as BLOCKED if needed.
2. Parse Greenhouse job HTML into canonical mission / requirements / benefits structurally, including headings "Your Qualifications", "Must-Have Skills", "Requirements", "Your Tasks", preferred/optional qualification subsections. Use HTML parser/normalization and synthetic fixtures; do not hallucinate job requirements. Original content can remain available as source provenance without contaminating normalized fields.
3. Guard ranking against unknown/incomplete required qualifications: missing/ambiguous/unparseable must never become verified GREEN merely because zero hard gates were detected. Record UNKNOWN or equivalent explicit unverified status; do not mark a mismatch RED without candidate evidence. Preserve useful score as indicative but not verified suitability. Ensure behavior also works for sources whose normalized requirements already exist (especially SpaceX).
4. Tests MUST include public job IDs 4997134101 and 4944174101 with required years/domain/degree text in synthetic public fixtures; assert no falsely verified GREEN for unknown/unsupported mandatory criteria, no false eligibility from keywords alone. Include positive proof for genuinely satisfied requirements, optional vs mandatory, empty HTML, malformed headings, no stated requirements, rerun idempotence and last-good preservation.
5. Do not access, copy or commit private candidate profiles, access tokens, actual personal applications or production data. Use synthetic candidate eligibility fixtures. Do not modify Hostinger/systemd, publisher timing, current datasets, or unrelated Mesabi adapter.
6. Run focused and full relevant tests, lint/compile and git diff --check. Commit code/tests/docs on isolated branch; push once and open ONE DRAFT PR referencing Issue #27. CI Ubuntu evidence required; fix real failures on same branch. Never merge or deploy without separate approval.
7. Post here: PR URL, commit SHA, tests/CI results, before/after false-GREEN demonstration for the two IDs, qualification parser coverage and unresolved risk. If tests or permission fail, mark BLOCKED, not DONE.

Definition of done: Auditable non-green guard for missing mandatory qualifications, reproducible tests including both RFA examples, green CI, one draft PR, no production changes.
```

---

Kein autonomes Mergen, Hostinger-Deployment oder Zugriff auf private Bewerberdaten. PR/Tests/Status im Paperclip-Task dokumentieren.

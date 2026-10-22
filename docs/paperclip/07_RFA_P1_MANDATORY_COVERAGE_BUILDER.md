# TASK 07 – RFA / PR #29: verpflichtende Kriterien einzeln absichern

**Ziel:** Verlässlich kein falsches `GREEN` für unbewertete zusätzliche Pflichtbedingungen, keine Pflicht-Gates aus rein optionalen Kriterien. Dieser Fehler ist durch Codeinspektion des existierenden PR #29 identifiziert, **nicht** als Produktionshäufigkeit gemessen.

**Anlegen:** Paperclip → VuTruLabs → Tasks → **New Task**. Alle vier Copy-Boxen **einzeln** kopieren. **Keinen neuen GitHub-PR oder Branch** erstellen, keine parallele Bearbeitung desselben Branches. Falls ein aktueller Agent bereits an PR #29 arbeitet, zunächst handoff/Koordination im bestehenden Task statt gleichzeitig pushen.

## Title

```text
JT-RFA-P1 – Close remaining false-GREEN and preferred-only gates in PR #29
```

## Assignee

```text
Builder
```

## Project

```text
Job Tracker Public
```

## Prompt

```text
ROLE: Builder — source-quality correctness follow-up on existing Greenhouse/RFA PR #29.

REPOSITORY: hailbagel/job-tracker-public
EXISTING PR ONLY: https://github.com/hailbagel/job-tracker-public/pull/29
EXISTING BRANCH: fix/vut-328-greenhouse-requirements
Reference head (verify current head before writing): 1ec94211c345a5fb1693f0a20d5f72b058db5f85
Review evidence and concrete counterexamples: https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6349563992

OBJECTIVE:
Resolve two untested logic gaps in the EXISTING PR without weakening conservative UNKNOWN semantics.

1. MANDATORY CLAUSE COVERAGE / FALSE GREEN:
analysis/profile_ranking.py currently sets recognized_requirements=true if ANY mandatory concept is recognized. If the same BASIC QUALIFICATIONS text includes an additional unrecognized MUST-HAVE criterion, it may still return GREEN when the recognized one is verified.
Create a deterministic negative fixture containing BOTH a verified bachelor's degree and an unmatched required driver's license. Status must not be GREEN when there is no license evidence. Include examples with mandatory engineering/PE license or other unrecognized obligations to prove general behavior, not merely a hard-coded driver's-license patch.
Design explicit mandatory criterion coverage / fail-closed UNKNOWN for uncovered basic clauses, while preserving evidence-backed verified statuses and the existing ranking schema. Do not assume all raw text is parseable or that some recognized qualifications prove full coverage. Prefer a clear UNKNOWN reason over speculative RED for missing candidate evidence.

2. PREFERRED-ONLY PARSE / FALSE HARD GATE:
analysis/profile_ranking.py split_qualifications(text) currently uses sections.get('basic') or _clean(text) even when the only recognized marker is PREFERRED QUALIFICATIONS. This wrongly feeds preferred-only clauses into basic hard-gate recognition.
Add fixture 'PREFERRED QUALIFICATIONS:\nBachelor\'s degree' and Greenhouse content with only preferred heading and role mission. A preferred-only requirement must not become a mandatory degree hard gate. No accidental GREEN solely because BASIC is absent; missing mandatory information must be treated conservatively as UNKNOWN where appropriate.

ACCEPTANCE / QUALITY:
- Original RFA 4944174101 and 4997134101 regressions continue to pass as UNKNOWN with exact hard-gate evidence.
- Missing/malformed/ambiguous required sections => UNKNOWN, never keyword-only GREEN.
- Additional unsupported/unverified mandatory condition next to satisfied degree => UNKNOWN or RED according to explicit evidence, never GREEN.
- Preferred-only criteria stay soft and cannot create hard gates.
- Positive fully-evidenced case remains GREEN when all mandatory criteria are truly covered; no blanket all-UNKNOWN regression.
- Run relevant fixture tests, full Python suites, both complete Ubuntu GitHub Actions, compileall, git diff --check. Report HEAD commit SHA, CI URLs, changed files, limitations, and updated ranking behavior.
- Request independent review of new commit only AFTER both full GitHub Actions workflows are green.

BOUNDARIES:
Use only the current existing PR #29 branch. Do not create duplicate PR or source adapter, do not access private candidate profiles, do not run Hostinger production commands, do not change scheduler, do not merge/deploy. Coordinate if another agent currently owns the branch; report BLOCKED rather than race with another writer. Preserve current approved code where possible; one focused repair cycle then report.
```

**Freigabe:** Paperclip-Abschluss ≠ Mergefreigabe. PR #29 neu reviewen, danach PR #30 gegen aktualisiertes `main` prüfen. Keine Hostinger-Freigabe enthalten.

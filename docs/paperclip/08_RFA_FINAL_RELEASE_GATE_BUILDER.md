# Paperclip Task 08 — Finales PR29 Ranking Release Gate (23.10.2026)

**Wozu:** VUT-341 hat die beiden alten Fehler behoben; VUT-344 hat den Commit unabhängig geprüft. **Nicht erneut anlegen!** Doch drei zusätzliche P1-Risiken aus dem vorigen unabhängigen Codex-Review sind im aktuellen Branch noch nachweisbar. Diese Aufgabe schließt diese Risiken in **demselben PR #29**, ohne die Systemarchitektur auszubauen. Ein P2-Parserfall wird gleichzeitig geprüft.

**WO:** Paperclip → VuTruLabs → Tasks → **New Task**, vier Felder **separat kopieren**. Falls bereits ein aktiver Writer auf PR #29 existiert, zuerst koordinieren statt parallel pushen. Keine neue GitHub-PR/Branch, kein Merge, keine Produktion.

## 1. Title

```text
JT-RFA-RELEASE-GATE – Verify degree field, work authorization and ranking cache in PR #29
```

## 2. Assignee

```text
Builder
```

## 3. Project

```text
Job Tracker Public
```

## 4. Prompt

```text
ROLE: Builder / GitHub engineering owner. Perform ONE final narrowly scoped correctness hardening cycle on the EXISTING PR #29, then stop for independent QA and explicit owner release.

REPO: hailbagel/job-tracker-public
PR: https://github.com/hailbagel/job-tracker-public/pull/29
BRANCH: fix/vut-328-greenhouse-requirements
Current baseline commit: 29b03a33f807d6e42d68d22491600d579769bf16 (recheck head)
Evidence comment: https://github.com/hailbagel/job-tracker-public/pull/29#issuecomment-6365211451

ALREADY DONE, DO NOT REIMPLEMENT:
- Paperclip VUT-341 fixed missed mandatory clauses and preferred-only sections. Independent QA VUT-344 passed.
- Latest two Ubuntu workflow runs for baseline commit passed: 39954763376 and 39954763521.
- Preserve RFA IDs 4944174101 and 4997134101, 123 focused tests claimed in task (reconfirm in CI), and existing schema/safety guarantees.

REQUIRED CODE+TEST SCOPE (P1):
A. SUBJECT-SPECIFIC DEGREE: Generic profile eligibility.degree.status=verified must NOT satisfy a requirement for a particular discipline (e.g., Aerospace Engineering). Require explicit trustworthy field/equivalence evidence matched to the job requirement or status UNKNOWN; do not invent that a generic bachelor's covers Aerospace Engineering. Keep a positive path for truly verified matching degree, and tests for nonmatching, matching and missing evidence.

B. JURISDICTION-SPECIFIC WORK AUTHORIZATION: Generic work_authorization=verified must NOT satisfy 'authorized to work in Germany' using evidence applicable only to the US (or vice versa). Match explicitly verified country/jurisdiction in a backward-compatible way; otherwise UNKNOWN, not GREEN. Preserve existing ITAR handling and red/unknown distinctions. Add Germany-vs-US negative test and positive country-specific test.

C. RANKING VERSION/CACHE: RUBRIC_VERSION in analysis/profile_ranking.py is unchanged at 2.0 although ranking semantics changed. generate() uses rubric_version in input_hash and can reuse the old on-disk document when snapshot/profile unchanged. Bump rubric version correctly and test unchanged source/profile + previously cached output => recomputation under new semantics, with no stale false-GREEN result.

ALSO REVIEW (P2):
D. Greenhouse plain heading 'Nice to Have' should be classified as PREFERRED; never convert subsequent optional criteria into BASIC hard gates. Include a heading-variant fixture.
E. Clause parser currently treats ANY recognized token as recognizing the whole mandatory clause; test one-line combined 'Bachelor's degree AND valid driver's license required' and fail CLOSED (UNKNOWN) for any unverified condition, even alongside a verified degree. Do not blindly mark all records UNKNOWN; preserve a legitimate fully-evidenced GREEN positive control.

RELEASE / EVIDENCE CONTRACT:
- Keep changes tightly scoped to this PR #29 branch and the needed parser, ranking, cache, profile schema and tests.
- 2 named RFA original-job regression tests; negative and positive cases for A/B/C/D/E; full Ubuntu workflows green, syntax compilation and git diff --check.
- Push to SAME PR #29, report final SHA, changed files, two CI URLs, and exact residual limitations. Do not claim measured accuracy from fixtures.
- Request independent PR CODE review on NEW HEAD, once; do not launch unlimited re-review loops.
- If some qualification categories are not explicitly modelled, return UNKNOWN with auditable reason rather than assume eligibility. Report bounded remaining limitations for future separate work.

HARD BOUNDARIES: No new branch, PR, Paperclip duplicate, Hostinger command, deployment, systemd change, production publisher, scraping, live collections or private candidate profile access. DO NOT MERGE. If another writer owns this branch, STOP and report coordination blocker.

DONE = implementation + evidence; release gate remains for owner after review. PR #30 integration, final merge order and Hostinger proof remain separate.
```

## Abnahme nach Builder

- Zwei erfolgreiche Ubuntu-Workflows am neuen SHA und unabhängiger PR #29-Review am neuen SHA.
- Änderungen vom bestehenden PR #30 dürfen nach PR #29 Merge nicht verloren gehen; erneute Integration/CI nötig.
- Hostinger-Betrieb bleibt separat: installierte Revision, Timer-Journal, persistenter Zustand, 3 geplante sechs-Stunden-Erfolge.

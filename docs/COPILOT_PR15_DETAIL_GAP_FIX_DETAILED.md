# Copilot Prompt — PR #15 P1: Reject Missing Detail Rows

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


Use this prompt only in the **hailbagel/job-tracker-public** repository.

> IMPORTANT: If VS Code is currently opened on another repository (for example `ESP32-Paxcounter`), STOP. Do not modify, stage, commit, stash, reset, or discard anything in that other repository. Open the `job-tracker-public` repository first, then run this task.

---

## Context

Repository:

```text
hailbagel/job-tracker-public
```

Existing PR:

```text
#15 — Normalize provider outputs and repair HyImpulse acquisition
```

Feature branch:

```text
fix/normalize-provider-data-hyimpulse
```

The previous P1 about preserving the HyImpulse one-time reset across failed/incomplete Personio attempts has already been fixed in commit:

```text
fef977ab347c6c7947fa52d7bd5d71f9e9ae1975
```

Do **not** redo that fix.

A new Codex review on the current PR head found a separate P1 in `jobtracker/pipeline.py`.

---

## New P1 finding to fix

Codex finding:

```text
Reject current jobs that lack detail rows
```

Current behavior in `normalize_existing_provider()` effectively allows this pattern:

```python
details = details_by_link.get(link, {})
```

That means if a current job exists in `jobs_latest.csv` but the legacy detail scraper failed to produce the matching row in `job_details.csv`, normalization can synthesize a canonical detail row with blank detail content.

This is unsafe because later validation sees a normalized detail row for every current link and may incorrectly classify an incomplete provider dataset as complete.

That can allow:
- incomplete source coverage to look successful;
- blank detail data to enter normalized outputs;
- inaccurate profile ranking;
- publication of a source snapshot that should have failed closed.

---

## Required behavior

For `existing_provider` normalization:

1. Every current job in `jobs_latest.csv` must have a corresponding detail row in `job_details.csv`.
2. Matching should use the existing stable/current link identity already used by the normalization code.
3. If any current latest-job link is missing from `details_by_link`, normalization must fail explicitly.
4. Do **not** create a replacement detail row from an empty mapping.
5. The provider must then follow the existing failure/last-known-good behavior rather than publishing an incomplete normalized dataset.
6. Do not weaken `validate_source_dataset()` or any publication safeguards.
7. Existing complete provider datasets must continue to normalize successfully.
8. Do not change the already-fixed HyImpulse reset-state behavior.
9. Do not change the canonical schema unless the concrete fix requires it; this P1 should normally be solvable without a schema change.

---

## Repository safety checks before editing

First verify the workspace and branch.

Run and show:

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
git fetch origin
```

Expected repository root must be the local checkout of:

```text
hailbagel/job-tracker-public
```

Expected working branch:

```text
fix/normalize-provider-data-hyimpulse
```

If you are not in that repository, STOP and tell me which repository is open.

If unrelated staged/untracked files are present, do not alter them.

Never stage or commit:

```text
patrick.json
private profile data
credentials
runtime/cache files
generated production datasets
unrelated local files
```

---

## Inspect before editing

Inspect at minimum:

```text
jobtracker/pipeline.py
jobtracker/processing.py
jobtracker/acquisition.py
tests/test_registry_pipeline.py
tests/test_provider_failures.py
tests/test_personio_xml.py
tests/test_profile_ranking.py
```

Locate:

- `normalize_existing_provider()`
- construction of `details_by_link`
- the current loop over latest/current jobs
- the current failure path for incomplete provider datasets
- existing tests for source normalization and last-known-good preservation

Before changing code, briefly explain:
- why the current empty-mapping fallback hides a missing-detail condition;
- where the smallest safe guard should be added;
- which existing failure path will handle the error.

---

## Implementation requirement

Make the smallest coherent fix.

Preferred behavior:

```python
if link not in details_by_link:
    raise ValueError(...)
```

or an equivalent explicit failure that fits the repository's existing error model.

The error should be specific enough to identify the provider and missing job/link during debugging, but do not expose private information.

Do not fabricate detail fields.

Do not silently drop the current job.

Do not convert the source to partial success.

The source should fail closed for that acquisition attempt and preserve the existing last-known-good tracked outputs through the already-existing publication/failure behavior.

---

## Required regression tests

Add focused tests that prove the exact bug and its fix.

### Test A — missing detail row fails

Construct a temporary existing-provider dataset where:

- `jobs_latest.csv` contains two valid current jobs;
- `job_details.csv` contains only one matching detail row;
- both latest jobs otherwise have valid identities/links.

Assert:

- normalization raises/fails explicitly;
- no fabricated blank detail row is produced for the missing job;
- the incomplete dataset is not represented as complete.

### Test B — complete detail coverage succeeds

Construct the same dataset with both matching detail rows.

Assert:

- normalization succeeds;
- overview/detail row counts match;
- canonical schemas remain correct.

### Test C — last-known-good preservation

Where practical using the existing orchestration/failure tests:

- start with an existing known-good normalized provider dataset;
- simulate a subsequent acquisition with a missing detail row;
- verify the failed attempt does not overwrite the last-known-good tracked provider outputs.

### Regression protection

Re-run the tests that protect prior work:

- HyImpulse Personio/reset-state tests;
- registry normalization tests;
- provider failure tests;
- SpaceX acquisition / metadata-to-ranking regression;
- Patrick feed tests.

Do not remove or weaken existing assertions just to make tests pass.

---

## Validation commands

Run the focused tests appropriate to the repository. At minimum include the relevant modules, for example:

```bash
python -m unittest   tests.test_registry_pipeline   tests.test_provider_failures   tests.test_personio_xml   tests.test_spaceX_acquisition   tests.test_patrick_multi
```

Use the actual existing module names/casing from the repository if they differ.

Also run the focused SpaceX profile-ranking regression test that protects:

```text
requisition_id
first_published
updated_at
```

Then run:

```bash
git diff --check
```

Do not run the production publisher.

Do not touch Hostinger.

Do not change systemd or the 48-hour scheduler.

---

## Review before commit

Before committing, show:

```bash
git status --short
git diff --stat
git diff --check
```

Then summarize:

- exact files changed;
- exact logic changed;
- exact tests added/updated;
- test results;
- confirmation that the previous HyImpulse reset-state fix remains intact;
- confirmation that `patrick.json` and unrelated files are not staged.

---

## Commit and push

If all focused tests pass:

1. Commit only the intended fix/test files to the **same branch**:

```text
fix/normalize-provider-data-hyimpulse
```

Suggested commit message:

```text
Reject incomplete existing-provider detail datasets
```

2. Push the same branch to origin.

3. Do NOT create a new branch.
4. Do NOT create a new PR.
5. Do NOT merge PR #15.
6. Do NOT deploy.
7. Do NOT touch production.

PR #15 should update automatically.

---

## Final response

Return only a concise implementation report containing:

- branch name;
- new commit SHA;
- exact files changed;
- focused test count/result;
- `git diff --check` result;
- whether the missing-detail P1 is fixed;
- confirmation that no merge/deployment occurred;
- confirmation that `patrick.json` was not committed.

Stop after push.

# Copilot Prompt — Normalize Provider Data and Repair HyImpulse

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


Copy the prompt below into **GitHub Copilot Chat in VS Code** while the repository root is open.

---

## Prompt

You are working inside the repository `hailbagel/job-tracker-public`.

Your task is to **normalize provider outputs around the repository's existing canonical schema and repair the current HyImpulse data-quality problem**.

### Important: understand the existing architecture first

Before changing any code:

1. Inspect:
   - `jobtracker/processing.py`
   - `jobtracker/acquisition.py`
   - `jobtracker/pipeline.py`
   - `configs/sources.json`
   - `scripts/publish_public_data.py`
   - the provider implementations under `scrapers/providers/`
   - representative files under `data/*/processed/`
   - the existing tests

2. Treat the schema already defined in `jobtracker/processing.py` as the current canonical normalized schema.

The important existing definitions are:

```python
LATEST_FIELDS = (
    "id",
    "source_id",
    "source_job_id",
    "title",
    "location",
    "company",
    "department",
    "link",
    "scrape_timestamp",
)

DETAIL_FIELDS = LATEST_FIELDS + (
    "mission",
    "requirements",
    "benefits",
)
```

**Do not create a second competing schema module such as `schemas/job_schema.py` unless you can prove the existing canonical schema cannot serve the requirement. Prefer one source of truth.**

### Problem 1 — inconsistent processed CSVs

The repository contains legacy processed datasets whose columns are not identical across providers.

Audit at least:

- `data/spacex/processed/`
- `data/neura/processed/`
- `data/jacobs/processed/`
- `data/tesla/processed/`
- `data/hyimpulse/processed/`
- `data/exolaunch/processed/`
- `data/rocket-factory-augsburg/processed/`

For each standard output:

- `jobs_latest.csv`
- `job_details.csv`
- `job_history.csv`
- `job_changes.csv`
- `department_summary.csv`
- `location_summary.csv`

determine whether the file matches the schema produced by the current shared processing layer.

The goal is that **new successful acquisitions produce consistent normalized files regardless of provider**.

Do not blindly rewrite historical data. If tracked legacy files need a one-time migration, make that explicit, deterministic, testable, and minimal.

### Problem 2 — HyImpulse currently reports success with bad data

Current HyImpulse data is structurally valid but semantically poor.

Observed examples include:

```text
title = APPLY NOW
location = Unknown
department = Unknown
mission = ""
requirements = ""
benefits = ""
```

The current registry entry uses `html_job_links`.

Investigate the actual HyImpulse / Personio public source and repair acquisition so that it captures the real job information.

Prefer a structured public Personio source/API/XML feed when available over scraping generic "Apply now" links.

For HyImpulse, a successful acquisition should provide, where exposed by the official public source:

- stable source job id
- real title
- location
- company
- department
- canonical job URL
- meaningful job description / mission
- requirements
- benefits when available

Do not fabricate unavailable values. Empty optional fields are acceptable; fake values are not.

### Design requirements

Keep the implementation simple.

- Reuse `jobtracker.processing.process_success()` wherever appropriate.
- Reuse existing acquisition adapters where possible.
- Add a reusable adapter only when it clearly reduces provider-specific code.
- Preserve `configs/sources.json` as the source registry.
- Preserve last-known-good data behavior on failed/incomplete acquisition.
- Preserve truthful `data/source_status.json` semantics.
- Preserve the Patrick feed behavior.
- Do not weaken publication validation.
- Do not modify Hostinger systemd files, scheduler cadence, SSH, credentials, or deployment configuration.
- Do not modify the 24-hour problem-source watcher unless required by a directly related documentation reference.
- Do not add `data/all_jobs.csv` as a new source of truth. If a consolidated dataset is useful, treat it only as a derived output and explain why before adding it.

### Tests

Add or update tests that prove:

1. normalized successful sources emit the canonical schemas;
2. extra provider-specific input fields do not leak into normalized CSVs unless intentionally part of the canonical model;
3. missing optional values normalize safely;
4. HyImpulse no longer emits `APPLY NOW` as every title;
5. HyImpulse produces real locations/departments when the official source exposes them;
6. failed or incomplete sources do not overwrite last-known-good normalized datasets;
7. existing SpaceX, NEURA, RFA, Exolaunch and Patrick-feed behavior remains intact.

Use fixtures/mocks for provider tests where possible. Do not depend on live internet access for the normal unit test suite.

### Workflow

Work directly in this VS Code workspace.

1. Inspect and explain the current mismatch first.
2. Give me a concise implementation plan before editing.
3. Then make the smallest coherent set of code/test changes.
4. Run the relevant tests.
5. Run `git diff --check`.
6. Show me:
   - files changed
   - tests run and results
   - remaining known limitations
   - whether any tracked data migration is required

Do **not** commit, push, merge, create a PR, alter production, or modify credentials. Stop after local code changes and verification so I can review the diff first.


---

## Follow-up Prompt — Final Review and Live HyImpulse Validation

Use this after the implementation pass above has completed and before committing anything.

```text
Before we commit anything, perform the final review/validation pass.

1. Do NOT make additional architectural changes unless required to fix a concrete failure.
2. Do NOT commit, push, create a PR, or touch production.

First show me the complete git diff summary and review the actual diff for unintended changes:

git status --short
git diff --stat
git diff --check

Then inspect every changed file and explicitly confirm:
- no second competing job schema was introduced;
- jobtracker/processing.py remains the canonical normalized schema;
- no production/scheduler/credential files were changed;
- configs/sources.json changes are limited to what is required for HyImpulse;
- existing SpaceX, NEURA, RFA, Exolaunch and Patrick-feed behavior is preserved;
- patrick.json remains untracked and untouched.

Then run ONE non-destructive live HyImpulse validation using temporary storage only.

The validation must:
- use the current HyImpulse registry configuration and acquisition code;
- write only to a TemporaryDirectory;
- not modify data/hyimpulse/processed;
- not publish;
- not commit;
- not push.

Print:
- total jobs returned;
- first 10 real job titles;
- first 10 locations;
- first 10 departments;
- number of rows whose title is exactly "APPLY NOW";
- number of Unknown locations;
- number of Unknown departments;
- number of rows with non-empty mission;
- number of rows with non-empty requirements;
- number of rows with non-empty benefits.

Fail the validation if:
- all titles are APPLY NOW;
- zero jobs are returned;
- the resulting overview/detail row counts differ.

After that, give me a FINAL REVIEW section containing:
- changed files;
- tests passed;
- live HyImpulse validation result;
- remaining limitations;
- whether the changes are safe to commit.

Stop there. Do not commit or push.
```


---

## Follow-up Prompt — Create Review Branch and Push Only

Use this after the final review reports that the changes are safe to commit.

```text
The implementation and final validation are complete.

Now prepare the changes for external review, but do not merge anything and do not touch production.

1. Show:
   git branch --show-current
   git status --short

2. Create a dedicated feature branch from the current working state if you are currently on main:
   fix/normalize-provider-data-hyimpulse

3. Stage ONLY the intended implementation/test/documentation files from this task.

4. Explicitly DO NOT stage or commit:
   - patrick.json
   - private profile files
   - credentials
   - runtime/cache files
   - generated production datasets
   - unrelated local files

5. Show the exact staged file list:
   git diff --cached --name-status

6. Run:
   git diff --cached --check

7. Commit with this message:
   Normalize provider outputs and repair HyImpulse acquisition

8. Push the feature branch to origin.

9. Do NOT merge.
10. Do NOT deploy.
11. Do NOT modify the production scheduler.
12. Do NOT create additional unrelated files.

At the end print:
- branch name
- commit SHA
- pushed remote branch
- exact committed file list
- confirmation that patrick.json was not committed

Stop after the push so the branch can be reviewed externally.
```


---

## Follow-up Prompt — Fix Review Blockers Before PR

Use this after branch `fix/normalize-provider-data-hyimpulse` was pushed at commit `d286abe10a79a98d6c134b59da013fb00f6f9513`.

```text
Do not open or merge a PR yet.

An external review of the pushed branch found two concrete behavioral regressions that must be fixed before review.

BRANCH
fix/normalize-provider-data-hyimpulse

CURRENT COMMIT
d286abe10a79a98d6c134b59da013fb00f6f9513

First fetch current main and inspect the exact branch diff. The branch is currently behind main by documentation-only commits, so rebase it onto origin/main before making the corrections if the working tree is clean.

BLOCKER 1 — job_changes history can be destroyed

Current flow for an existing_provider is:

provider writes current jobs_latest/job_details
-> legacy analysis.py updates accumulated history/change log
-> normalize_existing_provider()
-> process_success()

normalize_existing_provider() reads jobs_latest AFTER the provider has already overwritten it with the current snapshot. process_success() therefore treats the current snapshot as the previous snapshot for change detection.

It then writes canonical job_changes.csv from that derived result.

This can:
- produce an empty or incorrect current delta;
- overwrite the accumulated legacy job_changes.csv;
- destroy historical NEW/REMOVED/REACTIVATED events that are already tracked.

This is not acceptable.

Required behavior:
- historical change evidence must not be silently discarded;
- canonical normalization must preserve existing change history;
- future successful runs must append/preserve change events deterministically rather than truncate prior history;
- migration of legacy change rows must be explicit and tested;
- if a legacy change event has no trustworthy job id, do not invent a false provider-native id. A blank id is preferable to fabricated identity, while source_id/change/title/location/observed_at should be migrated truthfully where possible;
- rerunning normalization must not duplicate the same migrated historical events.

Add tests that start with a realistic accumulated legacy job_changes.csv and prove that normalization preserves prior rows and adds future changes without duplication.

BLOCKER 2 — SpaceX metadata used by the Patrick feed is silently dropped

The new canonical LATEST_FIELDS currently removes provider fields such as:

- requisition_id
- first_published
- updated_at

But analysis/profile_ranking.py::rank_job() explicitly reads these values and publishes them in SpaceX target records.

Normalizing SpaceX with the current branch would therefore silently turn previously available Patrick-feed metadata into null values.

That violates the requirement to preserve existing SpaceX / Patrick-feed behavior.

Fix this without creating a second schema.

Preferred approach:
- extend the one canonical schema in jobtracker/processing.py with generally useful optional fields required by downstream behavior, including:
  requisition_id
  first_published
  updated_at
- all providers must still emit the same canonical columns;
- providers without those values should emit empty strings;
- preserve the SpaceX values through normalize_existing_provider();
- do not add a SpaceX-specific second normalized schema.

If inspection finds other fields that an existing downstream consumer demonstrably reads from normalized jobs_latest/job_details, preserve them only when justified by actual current code. Do not expand the schema speculatively.

VALIDATION

After fixing both blockers:

1. Run the focused tests already used for this task.
2. Add tests proving:
   - legacy accumulated change history survives normalization;
   - future change events are appended without duplicating migrated history;
   - SpaceX requisition_id, first_published and updated_at survive canonical normalization;
   - profile ranking receives those SpaceX values after normalization;
   - HyImpulse still returns real titles/locations/departments/details;
   - canonical headers remain identical across providers.
3. Run git diff --check.
4. Run the non-destructive live HyImpulse TemporaryDirectory validation again.
5. Do not run production.
6. Do not modify systemd/scheduler/credentials.
7. Do not stage or commit patrick.json.

Then show a REVIEW FIX SUMMARY:
- exact files changed since d286abe...
- tests and results
- whether both blockers are fixed
- any remaining risks

If all checks pass, commit the corrections to the SAME feature branch and push it.

Do not merge and do not deploy.
Stop after pushing the corrected review branch.
```


---

## Clarification — HyImpulse Legacy Garbage May Be Discarded

```text
Clarification for the review-blocker fix:

The legacy HyImpulse processed data is known bad data (for example APPLY NOW titles, Unknown locations/departments, and empty detail fields). Preserving that historical HyImpulse change/history data is NOT a requirement.

For HyImpulse specifically:
- it is acceptable to start the normalized history/change tracking from the first successful clean Personio-based acquisition;
- do not spend effort migrating or preserving legacy HyImpulse garbage;
- do not carry APPLY NOW / Unknown legacy records into the new canonical history.

The historical-change preservation blocker applies to valuable legacy datasets from existing_provider sources such as SpaceX, NEURA, Jacobs, and Tesla where prior tracked history may contain useful evidence.

Keep the SpaceX metadata preservation requirement unchanged.
```


---

## Follow-up Prompt — Open Review PR Only

Use this after the corrected branch has been pushed at commit `abda14f6cf89bef9897b113a960eb24734ed2f89`.

```text
The corrected review branch is ready for pull-request review.

Branch:
fix/normalize-provider-data-hyimpulse

Current corrected commit:
abda14f6cf89bef9897b113a960eb24734ed2f89

Do not change implementation code unless creating the PR reveals a concrete branch/repository error.

Before opening the PR:

1. Fetch origin.
2. Confirm the branch is based on current origin/main and is not behind it.
3. Confirm the working tree has no unintended staged changes.
4. Confirm patrick.json is still untracked/private and will not be included.
5. Show:
   git status --short
   git log --oneline origin/main..HEAD
   git diff --check origin/main...HEAD

Then open ONE pull request from:

fix/normalize-provider-data-hyimpulse -> main

PR title:
Normalize provider outputs and repair HyImpulse acquisition

PR body must summarize:

- HyImpulse moved from html_job_links to the official public Personio XML feed.
- Current live validation returned 20 real HyImpulse jobs with:
  - 0 APPLY NOW titles
  - 0 Unknown locations
  - 0 Unknown departments
  - 20/20 non-empty mission, requirements and benefits
- Canonical normalized schema remains defined in jobtracker/processing.py.
- Canonical optional metadata now includes requisition_id, first_published and updated_at to preserve SpaceX/Patrick-feed behavior.
- Existing-provider normalization preserves and deduplicates useful legacy change history.
- HyImpulse intentionally discards the known-bad legacy APPLY NOW / Unknown history on the first successful Personio run, then preserves clean history afterwards.
- 33 focused tests passed.
- git diff --check passed.
- Full Windows profile-ranking export suite remains limited locally by the pre-existing directory-symlink privilege requirement; the focused SpaceX metadata-to-ranking regression test passed.
- No scheduler, Hostinger credential, deployment, production dataset, or private profile change is included.

Do not merge the PR.
Do not deploy.
Do not modify the production scheduler.
Do not commit patrick.json.

At the end return:
- PR number
- PR URL
- head commit SHA
- base branch
- confirmation that merge/deployment was not performed

Stop after PR creation.
```

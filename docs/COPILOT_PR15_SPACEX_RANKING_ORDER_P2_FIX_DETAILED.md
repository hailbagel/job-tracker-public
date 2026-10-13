# Copilot Prompt — PR #15 P2: Normalize SpaceX Before Ranking

Use this prompt only in the **hailbagel/job-tracker-public** repository and only on the existing PR #15 branch.

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

Current branch head:

```text
26ce9dad6a4419ad160ddc00b631f12920e4d723
```

The prior P1/P2 findings already fixed on this branch must remain intact:
- HyImpulse reset marker survives failed/incomplete Personio attempts.
- Existing-provider normalization rejects missing detail rows.
- Reactivated legacy history rows reconcile fallback IDs to trusted native IDs.

Do **not** redo those fixes.

## Remaining Codex P2

Codex finding:

```text
Normalize SpaceX before generating its ranking
```

Current problem:

`run_pipeline.py --company spacex` can run the profile-ranking export before canonical normalization is applied to the SpaceX processed files.

Normalization then changes semantic fields such as job IDs and canonical columns after the ranking has already been generated.

This can leave the directly generated SpaceX ranking stale relative to the final canonical `jobs_latest.csv` / `job_details.csv`, including a stale `processed_input_hash`.

The publication wrapper happens to regenerate the feed later, but direct pipeline runs should also be internally consistent.

## Required behavior

For a direct SpaceX pipeline run with a private ranking profile:

1. acquisition/provider processing completes;
2. canonical normalization completes;
3. only then should SpaceX profile ranking/export consume the normalized files;
4. ranking IDs and metadata must match the final normalized dataset;
5. `processed_input_hash` must describe the actual final normalized input used for the ranking;
6. do not run profile ranking twice unless unavoidable;
7. preserve existing behavior for providers that do not run SpaceX-specific ranking;
8. preserve Patrick-feed publication behavior;
9. do not weaken any current validation or fail-closed behavior.

Prefer the smallest orchestration change. If possible, move/reorder the normalization step rather than duplicating ranking logic.

## Inspect before editing

Inspect at minimum:

```text
run_pipeline.py
jobtracker/pipeline_steps.py
jobtracker/pipeline.py
jobtracker/processing.py
analysis/profile_ranking.py
tests/test_profile_ranking.py
tests/test_registry_pipeline.py
```

Before editing, explain briefly:
- where profile ranking currently executes;
- where normalization currently executes;
- why the current ordering makes the ranking stale;
- the smallest safe ordering change.

## Required regression test

Add focused coverage for a direct SpaceX pipeline execution that proves:

1. raw/provider SpaceX output exists;
2. normalization changes the relevant semantic representation to canonical values;
3. profile ranking runs after normalization;
4. exported ranking job IDs/metadata correspond to the canonical normalized files;
5. `processed_input_hash` matches the final normalized input;
6. no stale pre-normalization ranking remains.

Also ensure:
- existing SpaceX acquisition tests still pass;
- existing SpaceX metadata-to-ranking regression still passes;
- Patrick-feed tests still pass;
- HyImpulse Personio/reset tests still pass;
- missing-detail tests still pass;
- reactivation-history tests still pass;
- provider failure tests still pass.

Run:

```bash
git diff --check
```

## Safety

Do not modify:
- Hostinger;
- systemd/timer configuration;
- credentials;
- production datasets;
- private profile files;
- `patrick.json`.

Do not create a new branch or PR.

## Commit and push

If focused tests pass:

- commit to the SAME branch:
  `fix/normalize-provider-data-hyimpulse`
- suggested commit message:
  `Normalize SpaceX before profile ranking`
- push the same branch.

Do NOT merge PR #15.
Do NOT deploy.
Do NOT run the production publisher.

## Final response

Return only:
- branch;
- new commit SHA;
- exact files changed;
- focused test count/result;
- `git diff --check` result;
- confirmation the SpaceX ordering P2 is fixed;
- confirmation prior P1/P2 fixes remain intact;
- confirmation no merge/deployment occurred;
- confirmation `patrick.json` was not committed.

Stop after push.

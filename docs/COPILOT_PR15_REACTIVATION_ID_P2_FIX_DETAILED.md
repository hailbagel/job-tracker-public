# Copilot Prompt — PR #15 P2: Reconcile Reactivated Legacy History IDs

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

Current reviewed head:

```text
4ec3dd363a03defb9842d8ae18dc663d103e5470
```

The two previous P1 findings are already fixed. Do **not** redo them.

Codex now reports one remaining P2 in `jobtracker/processing.py`:

```text
Reconcile URL-derived history IDs when jobs reactivate
```

## Problem

During first normalization of a legacy existing-provider dataset, some inactive historical jobs may have no current provider-native ID mapping.

Those rows can receive a URL-derived fallback/hash ID.

Later, if the same posting reappears and the provider now exposes a native ID for that same link, the current migration logic may keep the old URL-derived ID because `_row_id()` prefers the already-stored history ID.

That can create a second history row for the same logical posting:

- old migrated row keyed by URL-derived ID;
- new current row keyed by provider-native ID.

This incorrectly resets `first_seen` and splits one logical job into two history records.

## Required behavior

When reconciling legacy history during normalization:

1. If a migrated history row has a link that now maps to a trusted current provider-native ID, use that current native ID for the migrated history row before keying/deduplicating history.
2. Preserve the original `first_seen`, prior `last_seen`, and active/inactive history semantics.
3. A reactivated posting must remain one logical history record rather than producing a duplicate row.
4. Do not invent provider-native IDs when no current trusted mapping exists.
5. URL-derived fallback IDs remain acceptable only where no trusted native mapping exists.
6. Do not change the already-fixed HyImpulse reset-state behavior.
7. Do not change the already-fixed missing-detail fail-closed behavior.
8. Do not modify scheduler, Hostinger deployment, credentials, production datasets, or `patrick.json`.

## Inspect before editing

Inspect at minimum:

```text
jobtracker/processing.py
tests/test_registry_pipeline.py
tests/test_personio_xml.py
tests/test_profile_ranking.py
```

Locate:

- `_row_id()`;
- construction/use of `previous_link_ids`;
- history migration loop;
- history keying/deduplication;
- reactivation/change-event logic.

Before editing, explain briefly:

- exactly why a migrated inactive row can keep the fallback/hash ID;
- where the native link->ID reconciliation should happen;
- why the fix preserves a single history record.

## Required regression test

Add a focused test for this exact sequence:

1. Start with a legacy historical row for a job link that is currently inactive.
2. On initial normalization, no native ID mapping exists for that link, so the migrated row uses a URL-derived/fallback ID.
3. On a later acquisition, the same link reappears and now has a trusted provider-native ID.
4. Normalize again.

Assert:

- there is exactly one history row for that logical job/link;
- the row is re-keyed/reconciled to the provider-native ID;
- original `first_seen` is preserved;
- current `last_seen` is updated correctly;
- active/reactivated state is correct;
- no duplicate old fallback-ID row remains;
- no duplicate reactivation/change event is created.

Also keep coverage for the fallback case:

- if no trusted native ID exists, the URL-derived ID remains stable.

## Regression protection

Re-run the focused suites that protect prior fixes:

- registry normalization tests;
- provider failure tests;
- Personio/HyImpulse reset-state tests;
- missing-detail rejection tests;
- SpaceX acquisition/metadata/ranking regression;
- Patrick feed tests.

Run:

```bash
git diff --check
```

Do not weaken tests to make them pass.

## Safety checks

Before committing, show:

```bash
git status --short
git diff --stat
git diff --check
```

Never stage or commit:

```text
patrick.json
private profile files
credentials
runtime/cache files
generated production datasets
unrelated local files
```

## Commit and push

If the focused tests pass:

- commit the fix to the SAME branch:
  `fix/normalize-provider-data-hyimpulse`
- suggested commit message:
  `Reconcile reactivated legacy history IDs`
- push the same branch to origin.

Do NOT:
- create a new branch;
- create a new PR;
- merge PR #15;
- deploy;
- touch production.

PR #15 should update automatically.

## Final response

Return only:

- branch name;
- new commit SHA;
- exact files changed;
- focused test count/result;
- `git diff --check` result;
- whether the P2 is fixed;
- confirmation that prior P1 fixes remain intact;
- confirmation that no merge/deployment occurred;
- confirmation that `patrick.json` was not committed.

Stop after push.

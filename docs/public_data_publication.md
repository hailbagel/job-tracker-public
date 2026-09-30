# Unattended public data publication

The manual and scheduled interface is the same command:

```bash
python3 scripts/publish_public_data.py
```

Engineering Operations should run it with `/opt/vutrulabs/job-tracker-public` as the working directory. For example, a systemd service uses:

```ini
WorkingDirectory=/opt/vutrulabs/job-tracker-public
ExecStart=/usr/bin/python3 scripts/publish_public_data.py
```

Host installation, the timer, repository credentials, and the private Patrick profile are Operations-owned. Provision the profile outside Git at `configs/private_profiles/patrick.json`, or set `JOB_TRACKER_PROFILE_PATH` to its absolute path. Do not put profile evidence or credentials in the repository or logs.

## Contract

- Enabled, automated sources in `configs/sources.json` are attempted independently. A failed source remains explicitly failed/incomplete; it does not block healthy sources outside its coverage scope.
- Patrick-feed contributors are enabled, automated `Space/Rocket` sources tagged `patrick`. Only successful contributors are published, and any failed contributor makes overall Patrick-feed coverage incomplete.
- Existing provider support for `neura`, `spacex`, `tesla`, and `jacobs` is preserved. Tesla, Jacobs, or NEURA failures do not block a healthy Patrick feed because they are not Patrick contributors.
- `data/source_status.json` and logs report attempted, successful, failed/incomplete, and published contributor source IDs plus overall Patrick-feed coverage.
- A nonblocking lock under `.runtime/publication/` serializes invocations.
- The command requires a clean worktree on `main` by default, fetches `origin/main`, rejects divergence, and performs only `git pull --ff-only origin main` before collection.
- Fresh, nonempty, schema-valid and link-coherent processed datasets are required. SpaceX acquisition metadata and the Patrick JSON/CSV/Markdown feed must agree with the collected SpaceX count.
- Only the explicit `OUTPUT_ALLOWLIST` in `scripts/publish_public_data.py` is staged. Raw snapshots, exports, caches, runtime state, private profiles, sessions, and credentials are excluded.
- Every allowlisted output must already be tracked in reviewed Git history. An untracked allowlist entry fails before collection; ignore rules are not treated as a publication boundary.
- No data change produces no commit. A changed publication commit records provider and Patrick counts, then pushes without force. Any push failure makes the command fail.

The defaults publish `HEAD:main`. `JOB_TRACKER_PUBLISH_BRANCH` changes the required checked-out local branch and `JOB_TRACKER_PUBLISH_REF` changes the remote ref for an explicitly approved branch-based operating model. If GitHub rejects `HEAD:main` because protected `main` disallows this publication actor, preserve the local commit and report that exact policy blocker to the CTO; do not weaken protection or force-push.

## Logs and recovery

Capture stdout and stderr with the host service manager. The command prints stages, validation failures, dataset counts, Git commands, and the local commit SHA after a push failure, but never prints credential values or Patrick profile contents.

Start diagnosis from the final `PUBLICATION FAILED:` line. Correct provider/runtime failures through Engineering Operations, then rerun the same command. For a push failure, the successful output commit remains local. Resolve credentials, branch protection, or remote history, then run the exact non-force command printed by the failure. Never reset or amend that unpublished output commit merely to rerun collection. Existing dirty worktrees and diverged history require deliberate reconciliation before the publisher will collect again.


The committed `acquisition.json` and Patrick feed files are safe bootstrap records with `publication_status` set to `awaiting_first_verified_production_run`. They establish reviewed, tracked publication paths without claiming production success. The first successful host run replaces them with complete validated outputs before committing.

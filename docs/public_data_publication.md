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

- Exactly `neura`, `spacex`, `tesla`, and `jacobs` are required. A disabled required provider or any failed pipeline stage fails the command.
- A nonblocking lock under `.runtime/publication/` serializes invocations.
- The command requires a clean worktree on `main` by default, fetches `origin/main`, rejects divergence, and performs only `git pull --ff-only origin main` before collection.
- Fresh, nonempty, schema-valid and link-coherent processed datasets are required. SpaceX acquisition metadata and the Patrick JSON/CSV/Markdown feed must agree with the collected SpaceX count.
- Only the explicit `OUTPUT_ALLOWLIST` in `scripts/publish_public_data.py` is staged. Raw snapshots, exports, caches, runtime state, private profiles, sessions, and credentials are excluded.
- No data change produces no commit. A changed publication commit records provider and Patrick counts, then pushes without force. Any push failure makes the command fail.

The defaults publish `HEAD:main`. `JOB_TRACKER_PUBLISH_BRANCH` changes the required checked-out local branch and `JOB_TRACKER_PUBLISH_REF` changes the remote ref for an explicitly approved branch-based operating model. If GitHub rejects `HEAD:main` because protected `main` disallows this publication actor, preserve the local commit and report that exact policy blocker to the CTO; do not weaken protection or force-push.

## Logs and recovery

Capture stdout and stderr with the host service manager. The command prints stages, validation failures, dataset counts, Git commands, and the local commit SHA after a push failure, but never prints credential values or Patrick profile contents.

Start diagnosis from the final `PUBLICATION FAILED:` line. Correct provider/runtime failures through Engineering Operations, then rerun the same command. For a push failure, the successful output commit remains local. Resolve credentials, branch protection, or remote history, then run the exact non-force command printed by the failure. Never reset or amend that unpublished output commit merely to rerun collection. Existing dirty worktrees and diverged history require deliberate reconciliation before the publisher will collect again.

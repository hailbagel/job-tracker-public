# Hostinger PR20: last successful run

Owner policy decision (20 October 2026): six-hour failed-attempt cooldown approved. Catch-up is approved only after the actual most recent successful publisher invocation is verified in the service journal. This is not approval to merge, deploy, restart units, or run a manual publication.

Copy the following read-only command into the Hostinger terminal:

```bash
journalctl -u vutrulabs-job-tracker-public.service --since '2026-10-15' --no-pager -o short-iso | grep -E 'Publication (committed and pushed|validated with no public changes)|No public dataset or feed changes|PUBLICATION FAILED|Deactivated successfully|Finished|Failed|Started|Starting' || true
```

The command prints relevant publication and service outcome records. It does not start or alter anything. A last Git commit is not evidence that no later unchanged-data run completed. If journal records are unavailable, do not invent a timestamp; use the conservative first-run policy from the existing PR20 runbook after separate approval.

Return only non-secret matching output. Do not run Hostinger deployment commands yet.
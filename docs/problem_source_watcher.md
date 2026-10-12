# Problem Source Watcher

## Purpose

This watcher supplements the production Job Tracker for public career sources that are currently degraded, unstable, or require additional monitoring.

It does **not** replace the existing Hostinger publication pipeline. The production pipeline, its 48-hour systemd schedule, publication safeguards, Git history, and Patrick Space/Rocket feed remain the authoritative automated collection path.

## Schedule

The watcher runs every 24 hours at approximately **10:00 Europe/Berlin**.

## Scope

Only these sources are monitored by this watcher:

| Source | Current condition | Watch objective |
| --- | --- | --- |
| NEURA Robotics | API path currently accessible; provider was previously failing because the legacy pipeline invoked Selenium after API collection | Verify the official public API remains reachable and that a reliable public job count can still be obtained |
| Tesla | Official careers State API and careers HTML returned HTTP 403 from the Hostinger environment | Detect whether the official/public source becomes accessible again or whether Tesla exposes a new legitimate machine-readable careers source |
| Jacobs | Official careers/SearchJobs path returned HTTP 202 access challenge from the Hostinger environment | Detect whether the official/public source becomes accessible again or whether Jacobs exposes a new legitimate machine-readable careers source |

## Baseline

Baseline established from live Hostinger checks on 2026-10-11/12:

### NEURA Robotics

- Public search-key/API path: accessible
- HTTP result: 200
- Live result observed: 203 jobs
- Public offer documents exposed rich fields including:
  - description
  - expectation
  - benefits
  - offering
  - about
  - introduction
  - additional
  - location
  - department
  - work_mode
  - salary
  - url
  - application_url
- PR #13 repaired the NEURA production collector so it no longer requires the generic Selenium detail stage.

### Tesla

- Official State API: HTTP 403 from the Hostinger environment
- Official careers HTML: HTTP 403 from the Hostinger environment
- Response classified as access denied
- No bypass is attempted.

### Jacobs

- Official careers site/SearchJobs path: HTTP 202 from the Hostinger environment
- Response classified as an access challenge
- No bypass is attempted.

## Daily behavior

Each scheduled check should:

1. Read the current repository state from:
   - `configs/sources.json`
   - `data/source_status.json`
   - this document
2. Check the relevant official/public source for NEURA, Tesla, and Jacobs.
3. Report:
   - source
   - current result/status
   - HTTP/result classification when available
   - reliable job count when available
   - whether the condition materially changed since the baseline or previous check
4. Send a concise daily ChatGPT summary.

## GitHub update policy

The watcher should **not create a Git commit every day**.

GitHub documentation/status should be updated only when there is a material source-condition change, such as:

- blocked -> accessible
- accessible -> blocked
- official source URL/backend changes
- a new reliable official machine-readable source is discovered
- failure classification materially changes
- a previously reliable source becomes incomplete
- a meaningful verified job-count/source-contract change requires documentation

No-change checks are reported in ChatGPT only.

## Safety and boundaries

The watcher must not:

- bypass CAPTCHA, anti-bot systems, authentication, or access controls
- modify scraper code automatically
- modify `configs/sources.json` automatically
- modify production datasets automatically
- change the Hostinger systemd scheduler
- change Git/SSH credentials or deployment access
- weaken publication safeguards
- overwrite last-known-good production data merely because a source is temporarily blocked

The watcher may inspect legitimate public/official sources and may update this documentation/status when a material condition changes.

If a source change requires code work, that work must follow the normal repository development path rather than being performed by the watcher.

## Relationship to production

The production Job Tracker remains responsible for:

- collection
- normalization
- history/change detection
- Patrick feed generation
- dataset validation
- Git publication
- 48-hour Hostinger execution

The Problem Source Watcher is an **observability and source-recovery layer** for difficult providers. It exists to detect when blocked providers become usable again and to surface source changes quickly without destabilizing production.

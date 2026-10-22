# Copilot task — Automate industrial & plant-engineering employer coverage

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


Repository: `hailbagel/job-tracker-public`  
Priority: P1 (SMS group), P1 (Midrex), P1 (Mesabi Metallics), P2 (Siemens AG).  
Date: 2026-10-15.

## Ground truth

The registry `configs/sources.json` now contains **four newly registered manual-discovery sources**:

- `sms-group` — SMS group — https://career.sms-group.com/de/jobs
- `midrex` — Midrex Technologies — https://www.midrex.com/careers/job-openings/
- `mesabi-metallics` — Mesabi Metallics — https://www.mesabimetallics.com/careers/
- `siemens` — Siemens AG — https://jobs.siemens.com/en_US/externaljobs

These are registry entries, **NOT automatically acquired/verified jobs**. Do not represent them as current production coverage or put their historical guesses into `data/`.

A previously verified production dataset, including SpaceX, HyImpulse, Exolaunch and the Space/Rocket Patrick feed, already passes the read-only data audit. Preserve its behavior. Siemens Energy is a **distinct employer**, not part of `siemens`. Do not mix their listings.

## Objective

Turn the four named industrial employers from discoverable/manual into **reliable automatically collected** sources, using official public endpoints or officially published job pages. Implement **one employer at a time**, starting with SMS group, under independently reviewable PRs. No mass rollout or Hostinger production deployment without explicit approval.

The tracker should support a *separate* industrial/plant engineering target category focused on construction execution, site management, plant projects, manufacturing, steel/iron production, direct reduction, heavy industry, interfaces and commissioning. Do not silently mix this category into the existing `Patrick Space/Rocket targets` report, whose semantics and contributor count must remain unchanged. Describe the smallest consistent design for additional industrial rankings, then implement it only after source acquisition and contractual review.

## Verified portal observations / implementation hypotheses (revalidate live)

### 1. SMS group — first implementation

Official job site: https://career.sms-group.com/de/jobs (powered by **d.vinci**).

d.vinci publishes documentation for a **Job Publication API**, including
`/jobPublication/list.json`, `/jobPublication/list.rss` and descriptions (`tasks`, `profile`, `weOffer`, `jobPublicationURL`, etc.):

https://static.dvinci-easy.com/files/d.vinci%20job-publication-api.html

**Do not assume the API is enabled or the default path works for the SMS custom domain.** First inspect the SMS portal's legitimately public network surface and its own navigation to establish the correct host and complete endpoint. The API documentation explicitly allows deactivated portal APIs (HTTP 403). If it is unavailable, report `manual_discovery` and inspect only permitted alternatives. Validate IDs, languages, detail fields, pagination and completeness. Record actual source count, not a search snippet.

### 2. Midrex Technologies — second

Official page: https://www.midrex.com/careers/job-openings/ — “View current openings” navigates to an official linked **Paycom** hiring portal.

Study publicly available listing/detail pages or authorized API/public feeds, stable posting IDs, pagination and any cross-location coverage. The JS-driven portal alone is not evidence of a complete machine interface. Do not scrape a candidate login, bypass access controls, or require authentication.

### 3. Mesabi Metallics — third

Official page: https://www.mesabimetallics.com/careers/ — shows vacancies (including construction and plant roles) and a location filter.

Determine whether official job records are in public page HTML, embedded structured data, a publicly served endpoint or a separate permitted ATS. The independently observed public page listed about **47 positions** at discovery time; this figure is **not a persistent completeness contract** and must never be hardcoded. Test canonical detail URLs/IDs, pagination, location filtering and descriptions; do not derive stable identity merely from title when an official job ID exists.

### 4. Siemens AG — fourth

Official jobs entry point: https://jobs.siemens.com/en_US/externaljobs (linked by https://www.siemens.com/de-de/company/jobs/).

Validate whether the Siemens job marketplace offers officially public paginated listings and full job details. Confirm request size/pagination and country/business filtering against total counts, avoiding truncated “999+” pages; do not mark global coverage complete when it is actually a geographic/business-unit subset. Separately identify Siemens AG vs Siemens Mobility subsidiaries in job metadata, and **exclude Siemens Energy** from this source.

## Architecture and safety gates

1. Inspect current `jobtracker/registry.py`, `jobtracker/acquisition.py`, `jobtracker/pipeline.py`, `jobtracker/processing.py`, `scripts/publish_public_data.py`, `scripts/audit_public_data.py`, `jobtracker/patrick.py`, `configs/sources.json`, tests and `PUBLIC_REPOSITORY_POLICY.md`.
2. Prefer reusable adapter implementations and fixture-driven tests; avoid four unrelated brittle per-employer scrapers if a generic documented adapter is suitable.
3. For each source, require canonical native ID, title, valid public URL, company, available location/department, details/provenance, complete accessible listing, validated pagination, and fail-closed upstream error reporting. No invented descriptions, fake 0-job success, silent partial pagination or duplicate listing inflation.
4. Preserve existing normalized public output contract: `jobs_latest.csv`, `job_details.csv`, `job_history.csv`, `job_changes.csv`, `department_summary.csv`, `location_summary.csv`, and `acquisition.json` where applicable.
5. **Before enabling each new automated source**: create a reviewed tracked output/bootstrap set, adjust publisher allowlist only as designed, satisfy its tracked-file and dirty-worktree prechecks, establish source-specific acquisition and ranking tests, and pass the read-only data audit. Do not turn a manual registry source directly to `api`/`ats` and leave missing output paths; that breaks unattended publishing.
6. Preserve previously published snapshots on failures. Do not silently count stale entries as current; no mass removals on upstream outage.
7. Never put private candidate evidence, credentials, access tokens, request cookies, user accounts, candidate applications or private raw exports into this public repo.
8. Do not bypass 401/403/429, CAPTCHAs, rate limits or prohibited crawling. Do not store personal application data. Respect publicly documented access.
9. Avoid polluting existing Space/Rocket ranking; add a separate **Industrial/Plant Engineering** category/feed as a dedicated design milestone and test its filters/counters. Make full-time employment distinct from freelance opportunities where available; do not imply vacancies are freelancer contracts.
10. Do not change Hostinger services, timers, private profiles, live `data/` files or schedule during this task; do not execute the production publisher.

## Required tests

For each automated source, add deterministic fixtures for complete listing, detail parsing, special characters, duplicates, empty listing, missing detail text, pagination, access denial, malformed upstream data, ID stability and preservation of previous good data. Run relevant integration tests for legacy providers, HyImpulse and Exolaunch, the Patrick feed and the publisher. Check `git diff --check` and report the exact result.

Acceptance before a source can go live:

- Verified authorized official source + repeatable finite, complete pagination or clearly scoped and declared coverage.
- Stable canonical IDs/URLs and correct multilingual descriptions.
- Repeat run without data changes does not manufacture adds/removes or duplicate history.
- Failures do not replace the last good snapshot; source status explicitly incomplete/failed.
- Source appears in the correct industrial category (not Space/Rocket).
- Production rollout is separately approved **after** code review, passing tests, GitHub commit/push and realistic cost/rate limit evaluation.

## Deliverable / workflow

1. First inspect and report a 4-row implementation feasibility matrix: source, real endpoint used, completeness proof, available descriptions, expected adapter, access restrictions and unresolved points.
2. **Build SMS group first**, branch + PR with code, fixtures, test output and no deployment. Do not merge without approval. If SMS is blocked, say exactly why and continue to the next source without a fake implementation.
3. Continue Midrex, Mesabi and Siemens in **separate PRs**, each with acceptance evidence.
4. Provide a separate architecture recommendation for industrial-target ranking/reporting and optional future employers such as **Siemens Energy**, Primetals Technologies, Tenova, Danieli and ANDRITZ. Those are candidates only; do not register or claim verified until reviewed.
5. Return GitHub PR URLs, commits, test results, source-scope limitations and remaining steps. All prompts and implementation decisions must stay versioned in Git, not only in chat.

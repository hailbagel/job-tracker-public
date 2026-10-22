# Work-laptop handoff — industrial employers (21 October 2026)

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


**Repository:** `hailbagel/job-tracker-public` (PUBLIC)  
**Audience:** VS Code Copilot coding agent on the Windows work laptop  
**Canonical base:** GitHub `origin/main` — never assume yesterday's local checkout is current  
**Primary task:** Establish genuinely automated, source-verified industrial career coverage, beginning with SMS group.  
**Previously committed source-analysis specification:** [COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md](COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md). Read it FIRST, then apply this newer operational handoff when the two differ.

## 1. Confirmed production baseline — DO NOT regress

- **PR #20** restart-safe hourly systemd eligibility timer + publisher gate was merged and deployed to Hostinger. Durable scheduler state is `/var/lib/vutrulabs-job-tracker-public/state.json`.
- **PR #21** fixed the history invariant: current SpaceX IDs and active history IDs now match after successful collection; historical records are preserved.
- **PR #22** changed the Python rolling-success eligibility to **6 hours**; six-hour failure backoff and hourly UTC systemd timer remain. Hostinger performed a guarded production run after updating to PR #22.
- The owner-provided Hostinger terminal output after the guarded 21 October run showed: **`AUDIT COMPLETE: 0 failures / 2 warnings`**, last-success state `2026-10-21T04:05:02.853171Z`, `Result=success`, `ExecMainStatus=0`, publisher service `inactive`, and the timer successfully restarted.
- Independently observed GitHub publication commit: **`316a612243fe5156828b45011e48422beb01fdf2`** at `2026-10-21T04:04:54Z`; results: SpaceX **2,779**, NEURA **207**, Rocket Factory Augsburg **55**, Exolaunch **11**, HyImpulse **32**, Patrick ranking **2,877**.
- Two surviving upstream limitations (not data-schema failures): Tesla collection HTTP **403**, Jacobs collection failure. Their retained records are explicitly stale (Tesla **8,117**, Jacobs **130**). Never treat stale records as fresh or bypass upstream access restrictions.
- **PR #17** — earlier full-data audit proposal — remains open, distinct from this assignment. Do not merge it incidentally.
- **The 6-hour cadence has been installed and one guarded execution verified; unattended repeated six-hour executions still require observation.** Do not claim that multiple automated cycles have already been witnessed based on this baseline.

The live `main` branch moves whenever the Hostinger publisher pushes public dataset changes. Always `fetch` and fast-forward before branching, and rebase/reconcile feature branches safely; never force-push shared branches or alter the public publisher's history.

## 2. Operator procedure on the Windows work laptop — before opening a Copilot coding task

1. In VS Code, **open the EXISTING cloned folder** `job-tracker-public` (File → Open Folder). If the repo is not yet cloned, use VS Code “Git: Clone” with the verified repository URL `https://github.com/hailbagel/job-tracker-public.git`, then open the clone. Do not initialize another repository over existing work.
2. Open **Terminal → New Terminal (PowerShell)** inside that repository.
3. Confirm the `origin` is `hailbagel/job-tracker-public`, review `git status`, and abort if there are **ANY** local modifications or untracked files; never overwrite, reset, clean, stash or discard unreviewed work automatically. If a dirty tree is reported, stop and show the owner.
4. For a clean tree, execute the following PowerShell code (also supplied directly by ChatGPT in the handoff message). The `git pull --ff-only` prevents merge commits or history rewrites:

```powershell
$ErrorActionPreference = "Stop"
$origin = (git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -notmatch "hailbagel/job-tracker-public(\.git)?$") { throw "STOP: wrong GitHub origin. Found: $origin" }
if (@(git status --porcelain=v1 --untracked-files=all).Count -ne 0) { throw "STOP: local edits/untracked files; review before switching or pulling." }
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "STOP: git fetch failed" }
git switch main
if ($LASTEXITCODE -ne 0) { throw "STOP: cannot switch to main" }
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw "STOP: non-fast-forward or pull failed" }
git status --short --branch
git log -1 --oneline
```

5. On successful sync, open this handoff and the linked 15 Oct industrial onboarding specification, then start a **NEW Copilot Agent chat** in VS Code titled `Job Tracker — Industrial Sources`. Previous Hostinger scheduler chats are closed tasks; do not contaminate this source-onboarding implementation with timer changes.

## 3. Copilot coding-agent instruction — start here

You are the technical lead implementing official/public career source adapters in `hailbagel/job-tracker-public`. **Read the complete** `docs/COPILOT_INDUSTRIAL_EMPLOYERS_ONBOARDING.md`, this handoff, `ENGINEERING_PRINCIPLES.md`, `PUBLIC_REPOSITORY_POLICY.md`, `jobtracker/registry.py`, `jobtracker/acquisition.py`, `jobtracker/pipeline.py`, `jobtracker/processing.py`, `scripts/publish_public_data.py`, `scripts/audit_public_data.py`, relevant tests and `configs/sources.json`. Do not infer how the publisher works from the legacy `configs/companies.json` alone.

### Task A — verify source feasibility; do not bluff

Assess **all four** existing manual-discovery entries (do not duplicate IDs):

| Order | ID | Official starting point | Observed portal |
|---|---|---|---|
| 1 | `sms-group` | https://career.sms-group.com/de/jobs | d.vinci, API enablement **unverified** |
| 2 | `midrex` | https://www.midrex.com/careers/job-openings/ | Official linked Paycom |
| 3 | `mesabi-metallics` | https://www.mesabimetallics.com/careers/ | Official public jobs page |
| 4 | `siemens` | https://jobs.siemens.com/en_US/externaljobs | Siemens AG jobs; **not Siemens Energy** |

Document each company's verified *current* official portal, legally/publicly accessible machine interface if one exists, authentication/access restrictions, pagination and total-count evidence, canonical native IDs and detail URLs, language/locale variation, descriptions, locations, categories, and an explicit completeness scope. Distinguish reproducible verified evidence from assumptions. An HTTP 200 response does not establish a complete listing. **No bypass** of access controls, CAPTCHA, 403, cookies/sessions, login or rate limits.

Produce a concise **four-company feasibility matrix** in a NEW `docs/` report in the feature branch with live evidence date and URLs. Do not silently convert an unavailable public API into an invented scraper.

### Task B — implement ONE safe adapter first (prefer SMS group)

- If the verified SMS source offers a genuinely permitted and complete public feed, implement the smallest reusable adapter in the canonical `jobtracker/acquisition.py` / registry architecture. Only change the source config when the acquisition and validation contract is ready.
- **If SMS cannot be validated**, keep `sms-group` as `manual_discovery`, clearly document the blocker, and continue feasibility/implementation with the next best official source. Never fake current coverage or incomplete pagination.
- Required fields include native stable IDs, title, official detail URL, company, available location, descriptions / mission / requirements / benefits if published, source provenance, deterministic deduplication and confirmed completeness.
- Use the existing **normalized output schema** and **fail-closed** semantics. Empty, blocked, truncated or malformed collection is incomplete/failed; preserve last-good snapshots and historical IDs.
- Preserve the PR #21 SpaceX active-history invariant and no-new/removed-events-on-identical-snapshot behavior.
- Do not silently insert industrial companies into `Space/Rocket` Patrick rankings. Propose a **separate industrial/construction ranking** and its intended fields; avoid implementing a giant new dashboard or production feed prematurely.
- Do not conflate Siemens AG with Siemens Energy, or assume employee vacancies are freelance project contracts.

### Task C — fixtures, reviewability and safe rollout plan

Implement deterministic fixture tests for: pagination/full coverage, stable IDs/URLs, locale/HTML quirks, actual descriptions, empty feeds, duplicates, malformed responses, 401/403/429, source disappearance, repeated identical acquisitions, historical reactivation and last-good preservation. No live API dependence in default unit tests.

**Stage code on a feature branch**, e.g. `feature/industrial-sms-dvinci`. The existing four manual entries should remain manual for production until the end-to-end publication prerequisites and public-output bootstrap/allowlist have been reviewed. It is acceptable to deliver a tested adapter + fixture contract first, then a separate owner-approved production enablement PR. Clearly flag what is not live.

On Windows, `tests/test_publication.py` can fail to import `fcntl` because the publisher targets Linux; do not add unsafe Windows compatibility hacks to production. Instead validate on **GitHub Actions Ubuntu** before proposing a merge. Run targeted tests, Linux full unittest suite, `python -m compileall`, `git diff --check` and report exact results. Ensure `requirements.txt` is sufficient. Only commit intended source code, fixtures, tests and documentation.

**PR flow:** commit to feature branch → `git push -u origin feature/... ` → open one **draft PR** against `main` → wait for Linux checks → review findings; no auto-merge or Hostinger commands. For Midrex, Mesabi Metallics, Siemens use separately reviewed PRs, not a large multi-provider PR. Never modify, commit or regenerate tracked `data/` in the onboarding PR. Never force-push or reset local/private work.

### Mandatory operating limits

- No direct Hostinger commands, SSH deployment, `systemctl` changes, scheduler or failure-backoff changes, or forced immediate production runs. The 6-hour live scheduler is stable and separate.
- No edits to existing public `data/` during discovery; use temporary test directories. Do not commit employee resumes, credentials, application records, private Patrick profile, token/cookies or machine configuration.
- Production publisher only stages **allowlisted, already tracked** normalized files; adding an adapter alone is **not** production integration. Before any go-live, explicitly plan source bootstrap files, allowlist, Patrick/non-Patrick feed behavior, tests, publication status and rollback. Obtain approval before enabling new automated source.
- Keep `main` deployable while the Hostinger publisher pushes datasets every 6 hours. Never put unreviewed adapter changes directly on `main`.
- Keep owner-facing workflow compact; deliver exact `git`/Copilot actions, test evidence and GitHub PR link. When blocked, return specific blocker with traceable evidence.

## 4. Initial deliverables required before the owner approves anything

1. Feasibility matrix (SMS, Midrex, Mesabi, Siemens; evidence/restrictions/coverage).  
2. One concrete working adapter or a documented no-go with next-source fallback.  
3. Git feature branch, commits and a **draft PR**, including fixture tests and Linux CI.  
4. Explanation of how a production source could be enabled later without breaking the publisher; identify all changed allowlist/bootstrap contracts.  
5. Separate concept for industrial/construction role ranking and role-type distinction.  
6. Status of the two existing Tesla/Jacobs access-related warnings; **no unrelated remediation** inside this scope.  

**Do not merge, deploy, start a source run, or change Hostinger settings. Ask for approval after returning the deliverables.**

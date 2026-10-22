# Copilot task — NEURA auxiliary CSV classification

> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.


Repository: `hailbagel/job-tracker-public`  
Evidence: Hostinger read-only public data audit on 13 October 2026, latest publication commit `21932010b4359d5446453baaf0c450623009d811`.

## Proven state

The audit finished with **0 failures / 3 warnings**. All 54 tracked public data files passed the current structural checks.

- NEURA canonical `data/neura/processed/jobs_latest.csv`: 204 current jobs
- NEURA canonical `job_details.csv`: 204 rows; `job_history.csv`: 349 rows
- Legacy auxiliary `data/neura/processed/jobs_structured.csv`: 181 rows
- `scripts/audit_public_data.py` warns about the difference but does **not** establish that the two files must have the same count.
- `scripts/publish_public_data.py` explicitly includes the auxiliary file in its public allowlist.
- `README.md` describes separate legacy provider-specific structured files followed by canonical normalization.
- Tesla and Jacobs failures are independent and out of scope.

## Goal

Determine whether `jobs_structured.csv` is a supported legacy intermediate/snapshot, a stale artifact accidentally left on the public allowlist, or a required data interface. **Do not assume unequal counts are a bug.**

## Required investigation (read only first)

1. Identify the exact producer and any consumers of `jobs_structured.csv` (including old scripts, tracked history, and document references).
2. Compare timestamps and semantics of its records with `jobs_latest.csv`; identify whether the 181 records represent an older snapshot, filtered fields, or an alternate contract.
3. Verify whether it is currently modified/published by a successful NEURA collection or merely retained unchanged.
4. Decide the minimum justified action:
   - keep and document explicitly as a legacy intermediate without false count-parity claims;
   - adjust the auditor to check the correct semantics; or
   - propose removing it from the public allowlist/versioned data **only if all consumers and historical contracts have been assessed**.
5. Ensure the authoritative current feed remains `jobs_latest.csv`, and preserve all 204 current jobs, 349 history records, 910 change records and correct publication metadata.

## Constraints

- No direct Hostinger changes, forced Git operations, dataset regeneration, scheduled service runs, privacy-impacting exports, or modification of the private Patrick profile.
- Never overwrite the 181 legacy rows with current 204 merely to silence the warning.
- Do not delete or rename production data without explicit approval.
- Do not broaden scope to Tesla, Jacobs or architecture refactors.
- Preserve the six normalized CSV schemas and existing tests.

## Deliverable and acceptance

Provide evidence-backed root cause, a before/after contract table, recommended disposition, minimal proposed file changes and focused regression tests. If a harmless code/documentation change is justified, implement it on a feature branch, test it, and create a PR for separate review; do not merge or deploy on your own.

The audit warning may only be removed or reworded when its true cause is verified, not because all files must numerically match.

## Following priorities

1. Investigate Jacobs source failures and legitimate public ATS access (stale retained 130 entries).
2. Investigate Tesla HTTP 403 without bypassing access controls (stale retained 8,117 entries).
3. Verify the next automatic 48-hour publication with evidence before claiming unattended production acceptance.

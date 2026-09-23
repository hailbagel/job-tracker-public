# Roadmap

Status is evidence-based. “Implemented” means repository behavior is covered by focused deterministic tests; “production verified” requires Engineering Operations evidence from the real host.

| Milestone | Status | Evidence / remaining gate |
| --- | --- | --- |
| Versioned source registry and reusable acquisition | Implemented | `configs/sources.json` contains the initial company pack plus legacy sources; API, ATS, web, existing-provider and honest manual-discovery dispatch are deterministic and tested. |
| Multi-company Patrick Space/Rocket feed | Implemented | Source-qualified aggregation reuses the evidence-backed rubric and hard gates, reports per-source coverage, preserves the SpaceX Louisiana subset, and strips private profile evidence from public exports. |
| Multi-provider public collection | Implemented | Required providers are explicit in `scripts/publish_public_data.py`; pipeline failures return nonzero. |
| SpaceX normalized acquisition and ranking | Implemented | Atomic acquisition/ranking code and focused tests are versioned on `main`. |
| Unattended public dataset and Patrick feed publisher | Implemented; awaiting technical acceptance | Serialized wrapper validates Git state, provider enablement, freshness, schema, coherence, tracked allowlist, commit behavior, and non-force push behavior. |
| Initial public output paths | Implemented | Processed datasets plus bootstrap acquisition/feed records are tracked and not ignored; bootstrap metadata explicitly does not claim a production run. |
| Host installation, credentials, and schedule | Not yet production verified | Engineering Operations must install and run the documented command from `/opt/vutrulabs/job-tracker-public`. |
| End-to-end production publication | Not yet production verified | Requires a successful real provider run, validated Patrick profile/feed, commit/push evidence, and scheduler evidence from Operations. |

The current production command and recovery contract are documented in [docs/public_data_publication.md](docs/public_data_publication.md). Branch protection or credential failures remain Operations/CTO blockers; protections must not be weakened to obtain a pass.

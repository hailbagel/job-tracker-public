# Public repository policy

This repository is VuTruLabs' public source of truth for the job-tracker software and its reproducible public-data pipeline.

## Intentionally public and versioned

- Application, scraper, analysis, pipeline, validation, and test source.
- Public provider configuration and setup/operating documentation.
- Processed public job datasets, normalized job outputs, and approved public Patrick Target Feed outputs.
- Architecture notes, roadmap/milestone status, non-sensitive validation evidence, and meaningful Git history.

Public outputs are reviewed before their paths enter the unattended publisher's explicit tracked-file allowlist. Runtime publication stages only that allowlist; `.gitignore` is defense in depth and is not relied on to protect already tracked content.

## Never public

- CV source files, Career Master source material, home addresses, private phone numbers, or other private personal data.
- Credentials, tokens, cookies, sessions, authentication material, or private application documents.
- Private source documents, private candidate profiles/evidence, raw crawler captures, caches, virtual environments, runtime locks/state, logs, or machine-specific files.

Private profile material belongs outside Git under `configs/private_profiles/` (or at an Operations-provisioned absolute path). Raw acquisition data belongs under ignored `data/*/raw/`; only validated processed outputs may enter the public allowlist. If classification is uncertain, do not stage or publish the material until the designated owner approves it.

## Publication control

Use `python3 scripts/publish_public_data.py` for manual and scheduled production runs. The command refuses dirty/diverged Git state, disabled required providers, stale/empty/incoherent outputs, untracked allowlist paths, and changes outside its explicit public allowlist. It never force-pushes or changes repository protections.

See [docs/public_data_publication.md](docs/public_data_publication.md) for the operational interface and [ROADMAP.md](ROADMAP.md) for evidence-backed delivery status.

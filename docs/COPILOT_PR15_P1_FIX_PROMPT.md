> **LEGACY / ARCHIV — VS COPILOT (22.10.2026):** Dieser frühere Copilot-Auftrag ist **keine aktuelle Arbeitsanweisung** und gehört **nicht** in Paperclip. Aktive Tasks sind separat in [Paperclip-Tasks – Title / Assignee / Project / Prompt](paperclip/README.md) dokumentiert. Nicht doppelt ausführen; kein Hostinger-Deploy.

PR #15 follow-up for Copilot.

Fix the unresolved P1 in jobtracker/pipeline.py: HyImpulse's pending one-time reset from legacy html_job_links data must survive failed or incomplete Personio attempts and be consumed only by the first successful complete Personio normalization. Add regression coverage for legacy -> failed Personio -> successful Personio -> second successful Personio. Preserve clean history after the first successful reset. Keep the work on fix/normalize-provider-data-hyimpulse, run the existing focused tests and git diff --check, then commit and push the same branch. Do not merge or deploy yet. Do not include patrick.json.

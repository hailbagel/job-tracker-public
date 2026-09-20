# SpaceX evidence-profile ranking

The normal SpaceX tracker path writes a stable, versioned personalized feed after successful acquisition, detail extraction, and tracker analysis. Candidate profiles and immutable private generations stay ignored. The unattended publisher validates an approved Patrick feed and copies its JSON/CSV/Markdown views to the tracked public processed-output paths defined by the repository policy.

## Dependency setup

From an ordinary checkout, create an isolated environment with the validated dependency versions:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "pandas==2.3.3" "requests==2.34.2" "selenium==4.49.0" "tqdm==4.70.1"
```

The validated interpreter is CPython 3.13.15. Confirm with `python --version`.

## One-time private profile setup

1. Copy `configs/profiles/example.json` to `configs/private_profiles/<profile-id>.json`.
2. Replace every synthetic claim with bounded evidence. Put only explicit years/domain, software, trade, and leadership facts in `qualification_evidence`; each claim needs `verified`, `unsupported`, or `unknown` status and provenance. Keep `status: "unknown"` and `evidence: null` whenever evidence is absent. `verified` requires a provenance object. Do not infer work authorization, ITAR eligibility, degrees, trades, software, years, domains, leadership, or metrics from job-text keywords.
3. Set `JOB_TRACKER_PROFILE_PATH` to that ignored file when its path is not `configs/private_profiles/patrick.json`.

The profile is local configuration; later runs do not require Paperclip or manual ranking. Other profiles are supported by setting `profile_id` and the environment path. Their output directory is derived from `profile_id` unless `--output-dir` is supplied to the ranking command.

## Normal run

From the repository root with dependencies installed:

```bash
python run_pipeline.py --company spacex
```

`--company` can be repeated. Omitting it retains the original all-enabled-companies behavior. On SpaceX, the overview provider obtains the complete Greenhouse `content=true` payload, atomically writes `jobs_latest.csv`, `job_details.csv`, and `acquisition.json`, and preserves the source job ID and URL. The browser detail step finds no missing SpaceX details and exits without starting WebDriver. The final normal-pipeline stage automatically writes:

```text
data/spacex/exports/<profile-id>/spacex_targets.json
data/spacex/exports/<profile-id>/spacex_targets.csv
data/spacex/exports/<profile-id>/spacex_targets.md
```

JSON is authoritative. CSV has the same ordered current records; Markdown is a human-readable summary with hard gates, soft gaps, fit reasons, role family, and profile focus for every displayed role. Run the ranking stage alone only for diagnosis or deterministic replay:

```bash
python analysis/profile_ranking.py --profile configs/private_profiles/patrick.json --require-profile
```

## Status and evidence policy

- `GREEN`: configured family, sufficient score, and every detected work-authorization, ITAR, degree-or-experience, required-years, domain, leadership, software, and trade gate has directly verified candidate evidence.
- `YELLOW`: relevant transferable or partial match without an unknown/unsupported hard gate.
- `RED`: outside configured families or at least one required gate is explicitly unsupported.
- `UNKNOWN`: relevant, but at least one detected hard gate lacks candidate evidence. UNKNOWN never enters verified strong targets.

Basic/minimum qualifications create hard-gate evidence. Preferred qualifications remain soft gaps. Job excerpts and candidate provenance are stored separately. Source job ID/URL—not requisition ID—is the identity key.

## Coverage, history, and no-churn

The provider replaces current acquisition files only when every nonempty API listing becomes a unique valid record. Empty, failed, or incomplete acquisition exits nonzero before replacing the prior good snapshot. Ranking also refuses incomplete or count-mismatched metadata and therefore cannot erase a valid prior feed.

`observed_at` records the latest successful acquisition clock. `data_changed_at` changes only when semantic job/detail content changes. Ranking hashes the semantic rows it actually reads from `jobs_latest.csv` and `job_details.csv`, plus profile evidence, rubric version, schema version, and the parsed semantics of `configs/profiles/schema.json`. Acquisition metadata is recorded but is not trusted as the cache identity. If meaning is unchanged, it preserves all three output files and their prior generation/source timestamps byte-for-byte. Execution-only scrape clocks and schema formatting-only changes are excluded. Material title, location, department, qualification, gate, years, trade/software, travel, shift, or profile-schema changes invalidate the result. A missing, unreadable, malformed, or structurally invalid profile schema fails the ranking run before publication and preserves the last good feed. Missing or corrupt CSV/Markdown companions are rebuilt from the canonical JSON without changing a valid generation timestamp; a damaged public JSON is recovered from the generation's private canonical copy.

Each export is written to an immutable sibling generation directory. The documented `data/spacex/exports/<profile-id>` path is an atomically replaced directory symlink. One open of the authoritative JSON is coherent by itself. A consumer that needs JSON, CSV, and Markdown from the same generation must resolve the directory symlink exactly once and use that pinned immutable directory for every open; resolving the moving symlink separately for each file can cross a publication.

Runnable multi-file consumer example:

```python
import csv
import json
from pathlib import Path

export_link = Path("data/spacex/exports/patrick")
generation = export_link.resolve(strict=True)  # Pin exactly once.
with (generation / "spacex_targets.json").open(encoding="utf-8") as handle:
    document = json.load(handle)
with (generation / "spacex_targets.csv").open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
markdown = (generation / "spacex_targets.md").read_text(encoding="utf-8")
```

Keep the pinned generation directory until all reads finish. Retention or cleanup must not remove a generation while any consumer may still be using its pinned path. A fresh consumer resolves the documented export link again and sees the generation current at that time.

Atomic publication is supported on Linux/POSIX filesystems that permit directory symlinks and atomic replacement of a directory entry in the export parent. The generation directories, temporary link, and documented export link must remain in that same filesystem parent. This implementation was tested on Linux only. On Windows, directory symlink creation may require Developer Mode or an appropriately privileged process, and filesystem replacement semantics may differ; Windows behavior was not validated. If symlink creation or replacement is unsupported or denied, the ranking command exits with an explicit error. With an existing feed, its last good pointer and generation remain available; without one, no documented feed path is published. A fully written but unreferenced staging generation may remain for later operational cleanup. The implementation does not silently fall back to sequential copies and does not instruct operators to change permissions. Use a supported environment instead. A failed pointer replacement likewise leaves the prior directory or symlink coherent.

The first personalized feed reports that prior personalized history is unavailable and does not label every existing role NEW. Later feeds report relevant jobs added, materially changed, and removed. Removed jobs remain only in the removal section and never in current strong targets. Ties are ordered by score descending, then title, location, source job ID, and URL.

## Verification and rollback

Focused verification:

```bash
python -m unittest -v tests.test_profile_ranking tests.test_spacex_acquisition
```

A real acceptance run must use the normal command, record the source observation time and hashes, and immediately replay the unchanged ranking stage to confirm identical bytes. Synthetic public output is under `examples/spacex_profile_ranking/`.

Rollback is to revert the reviewed VUT-238 correction commit after integration. This restores the prior ranking code, tests, schema, documentation, and synthetic examples while preserving processed history, private exports, and immutable export generations. Do not delete prior exports during rollback; keep them as historical evidence unless a separately authorized retention action says otherwise.

## Future approved integration

This issue delivers a private immutable branch and does not authorize public push, PR, merge, or publication. After the CTO/Chief of Staff separately approves and publishes the integration, an ordinary local checkout updates without copying Paperclip files:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
```

Use the actual approved integration branch in place of `main` if the later gate names a different branch.

# VUT-304 collector evidence and operator validation

## Official-source evidence

Bounded validation was performed on 2026-10-12 without CAPTCHA, access-control, or anti-bot bypasses.

- NEURA's [official careers portal](https://jobs.neura-robotics.com/) and an [official job page](https://jobs.neura-robotics.com/offer/software-engineer-interface-archite/d9bbac6a-ddb4-431c-8168-c2e77ca18453?showApplicationForm=false) expose the same rich job content returned by the portal's public `api.my-job-shop.com` Typesense documents. A single public document inspection confirmed `description`, `expectation`, `benefits`, `offering`, `about`, `introduction`, `additional`, structured location/department/work-mode/salary fields, and application/company/job URLs.
- Tesla's [official careers search](https://www.tesla.com/careers/search/) is the authoritative human-facing source. The exact State API used by the collector (`https://www.tesla.com/cua-api/apps/careers/state`) returned HTTP 403 in the collector environment. No reliable official machine-readable alternative was evidenced, so the provider remains `upstream_access_denied` and preserves last-known-good data.
- Jacobs' [official careers site](https://careers.jacobs.com/) is authoritative. Its exact official `en_US/careers/SearchJobs/` request returned HTTP 202 challenge HTML in the collector environment. No bypass was attempted, so the provider remains `upstream_access_challenge` and preserves last-known-good data.

## Bounded Hostinger validation after merge

Run exactly once from the merged checkout. It writes only to Python-managed temporary storage, does not publish, and does not mutate production data, services, the scheduler, credentials, or deployment state.

```bash
set -eu
cd /opt/vutrulabs/job-tracker-public
PYTHON=python3
"$PYTHON" -m unittest \
  tests.test_neura_typesense \
  tests.test_provider_failures \
  tests.test_profile_ranking.PipelineIntegrationTests \
  tests.test_publication.OrchestrationTests
"$PYTHON" - <<'PY'
import csv
import tempfile
from pathlib import Path

from scrapers.providers.neura_scraper import NeuraScraper

with tempfile.TemporaryDirectory(prefix="vut-304-neura-") as output:
    NeuraScraper("neura").run(data_root=output)
    processed = Path(output) / "neura" / "processed"
    with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
        latest = list(csv.DictReader(handle))
    with (processed / "job_details.csv").open(newline="", encoding="utf-8") as handle:
        details = list(csv.DictReader(handle))
    required = {
        "description", "expectation", "benefits", "offering", "about",
        "introduction", "additional", "work_mode", "salary", "application_url",
    }
    assert latest and len(latest) == len(details)
    assert required.issubset(details[0])
    print(f"NEURA temporary validation PASS: {len(latest)} overview/detail rows")
PY
printf 'Tesla official State API HTTP '
curl -sS -o /dev/null -w '%{http_code}\n' --max-time 20 \
  -H 'Accept: application/json' \
  'https://www.tesla.com/cua-api/apps/careers/state'
printf 'Jacobs official careers search HTTP '
curl -sS -o /dev/null -w '%{http_code}\n' --max-time 20 \
  -H 'Accept: text/html' \
  -H 'User-Agent: VuTruLabs-public-job-tracker/1.0' \
  'https://careers.jacobs.com/en_US/careers/SearchJobs/?4182=%5B76515%5D&4182_format=4422&listFilterMode=1&jobRecordsPerPage=100&jobOffset=0'
```

Expected classifications at the time of implementation: Tesla HTTP 403 -> `upstream_access_denied`; Jacobs HTTP 202 -> `upstream_access_challenge`. Any different status should be investigated as a new source condition, not treated automatically as complete zero-job coverage.

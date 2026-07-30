# 🤖 Job Intelligence Pipeline

An automated Python-based pipeline for collecting, structuring, and analyzing public job postings — designed for AI-powered hiring intelligence and market research.

---

## ✨ What This Project Does

This project continuously monitors public career pages and transforms unstructured job postings into structured, analyzable datasets.

Instead of manually browsing hundreds of job listings, the pipeline automatically:

- scrapes job overviews
- opens detailed job pages
- extracts relevant content
- tracks historical changes
- builds structured datasets for AI analysis

---

## 🧠 Vision

The long-term goal is to create an AI-ready job intelligence system capable of answering questions like:

- Which departments are growing fastest?
- What technologies are companies hiring for?
- How does hiring evolve over time?
- Which jobs best match my profile?
- What trends can be identified from hiring behavior?

---

# 🏗️ Architecture

```text
Public Career Website
        ↓
Overview Scraper
        ↓
Raw Snapshots
        ↓
Detail Page Scraper
        ↓
Structured Job Database
        ↓
Analytics / AI Layer
```

---

# 📁 Project Structure

```text
job-tracker/
│
├── run_pipeline.py                 # Orchestrator for all companies
│
├── scrapers/
│   ├── runner.py                   # Loads and runs company-specific scrapers
│   ├── job_details_scraper.py      # Opens job detail pages
│   ├── base/
│   │   ├── base_scraper.py         # Base class
│   │   └── base_detail_scraper.py
│   └── providers/
│       ├── tesla_scraper.py        # Tesla State API Scraper
│       ├── tesla_details.py        # Tesla detail parser
│       ├── neura_scraper.py        # Neura Scraper
│       └── neura_details.py
│
├── analysis/
│   ├── analysis.py                 # Analytics & history tracking
│   ├── export_txt.py               # TXT export
│   └── clean_data.py               # Text cleaning utility
│
├── configs/
│   └── companies.json              # Active companies configuration
│
├── setup/
│   └── init_scraper_architecture.py # Cleanup & reset tools
│
├── data/
│   ├── tesla/                      # Tesla data
│   │   ├── raw/
│   │   ├── processed/
│   │   └── exports/
│   ├── neura/                      # Neura data
│   │   ├── raw/
│   │   ├── processed/
│   │   └── exports/
│   └── spacex/                     # SpaceX data (coming soon)
│       ├── raw/
│       ├── processed/
│       └── exports/
│
└── README.md
```

---

# ⚙️ Core Components

## `run_pipeline.py`

Main orchestrator for the complete pipeline.

Loads config from `configs/companies.json` and runs the following steps for each company:

1. **OVERVIEW SCRAPER** → `scrapers/runner.py`
   - Scrapes all job listings
   - Writes raw and processed CSVs

2. **DETAIL SCRAPER** → `scrapers/job_details_scraper.py`
   - Opens each job detail page
   - Extracts structured content

3. **ANALYSIS** → `analysis/analysis.py`
   - Calculates statistics
   - Saves job_history.csv, department_summary.csv

4. **TXT EXPORT** → `analysis/export_txt.py`
   - Exports structured jobs as TXT files

### Usage

```bash
python run_pipeline.py
```

---

## `scrapers/runner.py`

Dispatcher for company-specific scrapers.

Loads scraper class from `scrapers/providers/` based on company name.

### SCRAPER MAP

```python
SCRAPER_MAP = {
    "tesla": TeslaScraper,
    "neura": NeuraScraper,
    "spacex": SpaceXScraper  # TODO
}
```

---

## `scrapers/providers/tesla_scraper.py`

Fetches the Tesla State API and parses job listings.

### Endpoint

```
https://www.tesla.com/cua-api/apps/careers/state
```

### Features

- API-based (no Selenium/browser needed)
- Maps lookup tables (locations, departments, types)
- Saves `jobs_latest.csv` and raw snapshot
- Robust SSL error handling

### Output

```
data/tesla/raw/tesla_jobs_raw_<timestamp>.csv
data/tesla/processed/jobs_latest.csv
```

---

## `scrapers/providers/neura_scraper.py`

Placeholder for Neura scraper.

(Implementation pending)

---

## `scrapers/job_details_scraper.py`

Opens each job detail page with Selenium and extracts structured content.

### Configuration

**Set TEST LIMIT:**

Open [job_details_scraper.py](job_details_scraper.py) lines 18-20:

```python
# ========================================
# TEST LIMIT
# ========================================

TEST_LIMIT = 5  # ← Change here: 0 = unlimited, 5 = only first 5 jobs
```

Options:
- `TEST_LIMIT = 0` → scrape all jobs
- `TEST_LIMIT = 5` → only first 5 jobs (quick for testing)
- `TEST_LIMIT = 100` → first 100 jobs

### Usage

```bash
# Tesla detail scraper (max 5 jobs, ~20 seconds)
python scrapers/job_details_scraper.py tesla

# Scrape all Tesla jobs (unlimited)
# Change TEST_LIMIT to 0
python scrapers/job_details_scraper.py tesla
```

### Features

- Incremental: saves already scraped jobs
- Duplicate prevention: skips known links
- Selenium Edge browser
- Timeout handling
- Saves: title, location, company, department, mission, requirements, benefits

### Output

```
data/<company>/processed/job_details.csv
```

---

## `analysis/analysis.py`

Calculates statistics and historical snapshots.

### Output

```
data/<company>/processed/department_summary.csv
data/<company>/processed/location_summary.csv
data/<company>/processed/job_history.csv
data/<company>/processed/job_changes.csv
```

---

## `analysis/export_txt.py`

Exports structured jobs as formatted TXT files.

### Output

```
data/<company>/exports/<company>_job_details_<timestamp>.txt
```

---

## `configs/companies.json`

Configures which companies are active.

```json
[
  {
    "name": "tesla",
    "enabled": true
  },
  {
    "name": "neura",
    "enabled": true
  },
  {
    "name": "spacex",
    "enabled": false
  }
]
```

Only companies with `"enabled": true` will be scraped.

---

## `setup/init_scraper_architecture.py`

Cleanup & reset script.

Deletes and recreates:
- `data/tesla`
- `data/spacex`
- Old scraper files

Untouched:
- `data/neura`

### Usage

```bash
python setup/init_scraper_architecture.py
```

---

# 🗂️ Data Layers

## 🔹 Raw Layer

Immutable historical snapshots.

These files are never overwritten.

Example:

```text
jobs_raw_2026-06-09_16-19-01.csv
```

---

## 🔹 Processed Layer

Structured datasets optimized for analytics and AI workflows.

Examples:

```text
jobs_latest.csv
job_details.csv
job_history.csv
```

These files may be updated over time.

---

# 🧪 Testing & Configuration

## Test Limits for Fast Development

### Job Details Scraper Test Mode

To avoid waiting hours for full scraper runs:

**File:** [scrapers/job_details_scraper.py](scrapers/job_details_scraper.py), lines 18-20

```python
TEST_LIMIT = 5  # Change here for test limit
```

**Options:**

| Value | Behavior | Duration |
|-------|----------|----------|
| `0` | Scrape all jobs (unlimited) | 1-4 hours |
| `5` | Only first 5 jobs | ~20 seconds |
| `20` | First 20 jobs | ~1:20 minutes |
| `100` | First 100 jobs | ~6:40 minutes |

### Quick Test Workflow

1. **Scrape Tesla overview** (5 seconds)
   ```bash
   python scrapers/runner.py tesla
   ```

2. **Only 5 details** (20 seconds)
   ```bash
   # TEST_LIMIT = 5 in job_details_scraper.py
   python scrapers/job_details_scraper.py tesla
   ```

3. **Test export** (1 second)
   ```bash
   python analysis/export_txt.py tesla
   ```

**Total time:** ~26 seconds

---

## Enabled Companies

Configure in [configs/companies.json](configs/companies.json):

```json
[
  {
    "name": "tesla",
    "enabled": true   # ← true/false to enable/disable
  },
  {
    "name": "neura",
    "enabled": true
  },
  {
    "name": "spacex",
    "enabled": false
  }
]
```

Only companies with `"enabled": true` will be executed.

---

## Data Cleanup

To reset all data:

```bash
python setup/init_scraper_architecture.py
```

This deletes and recreates:
- `data/tesla/` (empty)
- `data/spacex/` (empty)
- `data/neura/` is NOT deleted



This project can later be extended for:

- hiring intelligence
- competitive analysis
- talent market monitoring
- AI-based job ranking
- semantic search
- skill extraction
- embedding pipelines
- trend analysis
- dashboard visualizations

---

# 🧰 Technologies

- Python
- Selenium
- Pandas
- Git

---

# ✅ Current Features

- [x] Multi-company scraper architecture
- [x] Tesla State API scraping (no Selenium needed)
- [x] Neura Scraper (placeholder)
- [x] Detail page scraping with Selenium Edge
- [x] Incremental crawling (don't re-scrape)
- [x] Historical snapshots (immutable raw layer)
- [x] Structured CSV datasets
- [x] Duplicate prevention
- [x] Department & location analytics
- [x] TXT export with job details
- [x] Test limits for quick development
- [x] Configurable company enable/disable
- [x] Full pipeline orchestration
- [x] Data cleanup & reset tools

---

# 🚀 Future Ideas

- SpaceX scraper implementation
- AI-powered job evaluation
- Personal job matching
- Semantic embeddings
- Vector search
- Trend forecasting
- Dashboard UI
- SQLite/PostgreSQL backend
- Automated daily reports
- Job change tracking
- Skills extraction


---

# 📌 Notes

This project is intended for research, analytics, and educational use with publicly accessible job postings.

The pipeline is designed with responsible scraping principles such as:

- moderate request frequency
- incremental updates
- avoidance of unnecessary traffic
- public-data-only collection

---

# 👨‍💻 Status

Currently under active development as a personal AI/data engineering project focused on automation, analytics, and intelligent information extraction.

## Company Configuration

Each company may have its own config file.

Example:

configs/jacobs.json

{
  "enabled": false,
  "country": "United States",
  "records_per_page": 100
}

## Jacobs Configuration

File:

configs/jac

## Jacobs Configuration

File:

configs/jacobs.json

Example:

{
    "enabled": true,
    "country": "United States",
    "country_id": 76515,
    "records_per_page": 100
}
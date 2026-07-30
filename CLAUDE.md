# Engineering Rules

Prefer:

- Simple solutions
- Existing patterns
- Small commits
- Minimal dependencies
- Explicit code

Avoid:

- Premature abstractions
- Hidden behavior
- Complex frameworks
- Magic configuration

# Project Architecture

Current Companies:

- Tesla
- Neura

Planned Companies:

- SpaceX

# Provider Rule

Company-specific logic belongs in:

scrapers/providers/

Examples:

- tesla_scraper.py
- neura_scraper.py
- spacex_scraper.py

- tesla_details.py
- neura_details.py
- spacex_details.py

Core pipeline must remain generic.

Avoid hardcoded company logic in shared pipeline code.

# Data Rules

Store data in:

data/<company>/

Structure:

raw/
processed/
exports/

Never create new top-level folders without approval.

# Change Rules

Implement directly for:

- Bug fixes
- Small features
- Refactoring within existing architecture

Require approval for:

- New dependencies
- New storage formats
- Folder restructuring
- Data deletions
- Breaking changes

# Business Goal

Build a scalable Job Intelligence platform.

Priorities:

1. Reliability
2. Data Quality
3. Automation
4. Scalability
5. Commercialization

# Encoding Rules

Prefer ASCII characters in source code.

Use:

- ue instead of ü
- oe instead of ö
- ae instead of ä

Avoid:

- Emojis in console output
- Special Unicode characters in source code

# Pipeline Rule

The pipeline consists of:

1. Overview Scraper
2. Detail Scraper
3. Analysis
4. Export

Changes should preserve the existing pipeline structure.

Avoid bypassing pipeline stages unless explicitly required.

# Data Compatibility

When modifying code:

- Preserve existing CSV schemas
- Preserve column names
- Preserve existing analysis outputs
- Preserve backward compatibility whenever possible

Do not change CSV formats without approval.

# Response Style

Prefer:

- Complete files
- Copy-paste ready code
- Explicit file paths
- Concrete implementation

Avoid:

- Partial snippets when a full file is requested
- Abstract examples without implementation

# Current Project Status

Current State:

- Tesla overview scraper operational
- Tesla State API operational
- Tesla detail parser operational
- Neura detail parser operational
- Dynamic provider loading operational
- Analysis pipeline operational
- TXT export operational
- Job history tracking operational
- Job change tracking operational

Pipeline Status:

- Neura: Production Ready
- Tesla: Production Ready
- SpaceX: Planned

# Testing Rules

After modifying pipeline logic:

Run:

python run_pipeline.py

Verify:

- Overview Scraper
- Detail Scraper
- Analysis
- Export

All steps must complete successfully.

# Logging Rules

Prefer:

- Explicit status messages
- Detailed pipeline output
- File paths in logs

Use:

- [OK]
- [WARN]
- [ERR]

Avoid silent failures.

# CSV Rules

CSV files are considered system interfaces.

Do not change:

- Column names
- File names
- Folder structure

without approval.

New columns may be added only if backward compatibility is preserved.

# Change Tracking

The following files are critical:

- job_history.csv
- job_changes.csv

Preserve:

- Historical job records
- Active/inactive tracking
- New job detection
- Removed job detection
- Reactivated job detection

# User Preferences

The user prefers:

- Practical solutions
- Detailed explanations when debugging
- Complete copy-paste-ready files
- Clear folder structures
- CSV-based workflows
- Minimal dependencies
- Reusable scripts
- Transparent workflows

Avoid:

- Overengineering
- Unnecessary abstractions
- Framework migrations
- Large refactors without clear benefit
- Placeholder code when real implementation is possible
# PAPERCLIP TASK – Top-10-Ranking unabhängig gegenprüfen

**STATUS:** JETZT PARALLEL, Chief of Staff, READ-ONLY. **Ziel:** Paperclip → VuTruLabs → New Task. Jeden der folgenden vier Codeblöcke **einzeln** in das zugehörige Feld kopieren. **Nicht** in VS Copilot. Noch kein Paperclip-Task durch diese Repo-Datei angelegt.

## Title
```text
JT-TOP10-QA – Verify ranking evidence against official job postings
```

## Assignee
```text
Chief of Staff
```

## Project
```text
Job Tracker Public
```

## Prompt
```text
Role: Independent reviewer / Chief of Staff, VuTruLabs Paperclip.
Task: JT-TOP10-QA – independent public evidence QA for ranking trust.
Repo: https://github.com/hailbagel/job-tracker-public
Reference defect: https://github.com/hailbagel/job-tracker-public/issues/27
Do not reuse or claim findings from misassigned Paperclip task VUT-318.

1. Read the tracked 2026-10-21 public ranking snapshot top_25 (first ten entries). Record the exact snapshot timestamp and rank/job ID from that public file, not from live scraped market assumptions.
2. For each of exactly ten listings, fetch its official PUBLIC original job posting via a permitted browser/web tool, if still online. Record date/access, status and whether text is available. Do not bypass anti-bot protection, logins, challenges, or robots. If changed/removed mark UNVERIFIABLE and preserve snapshot evidence.
3. Compare public ranking explanations with original job requirements. Identify degree, mandatory experience, authorization/ITAR, hard domain requirements, licenses, work location and optional/preferred criteria. Do not guess the user's private qualifications or declare eligibility without verified data; this is an evidence-quality review, not a personal background scan.
4. Flag evidence failures: mandatory qualification omitted, unknown or empty requirements, status GREEN despite missing verification, ranking points that do not establish hard eligibility, URL/ID mismatch and old snapshot. Distinguish verified defects from source changes and unknowns.
5. Deliver a ten-row QA table with job ID, employer/title, original URL, extracted mandatory requirements, ranking-status/known gates, discrepancy severity, checked-at and evidence. Provide findings count only for this sample; do not generalize accuracy to all jobs. Call out the two known RFA IDs explicitly and quantify how many of the TEN were checkable.
6. Do not edit code, create duplicate implementation tasks, commit profile data, open PR, merge, apply for jobs, or activate Hostinger. Provide suggested acceptance criteria for CTO's Issue #27 PR. Avoid real candidate PII.
7. Post a compact PASS/RISK/BLOCKED summary with all ten evidence links and uncertainties into THIS task; stop.

Done: independent public ten-job audit, transparent unknowns, no changes to production.
```

---

Kein autonomes Mergen, Hostinger-Deployment oder Zugriff auf private Bewerberdaten. PR/Tests/Status im Paperclip-Task dokumentieren.

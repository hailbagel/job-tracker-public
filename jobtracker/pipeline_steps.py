BASE_STEPS = (
    {"name": "OVERVIEW SCRAPER", "script": "scrapers/runner.py"},
    {"name": "DETAIL SCRAPER", "script": "scrapers/job_details_scraper.py"},
    {"name": "ANALYSIS PIPELINE", "script": "analysis/analysis.py"},
    {"name": "TXT EXPORT", "script": "analysis/export_txt.py"},
)


def steps_for_company(company):
    """Return production stages without browser details for API-complete NEURA."""
    steps = [
        step for step in BASE_STEPS
        if not (
            company.lower() == "neura"
            and step["script"] == "scrapers/job_details_scraper.py"
        )
    ]
    if company.lower() == "spacex":
        steps.append({
            "name": "PROFILE RANKING EXPORT",
            "script": "analysis/profile_ranking.py",
        })
    return steps

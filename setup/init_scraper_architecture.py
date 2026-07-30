import os
import shutil

print("\n========================================")
print("SCRAPER FULL CLEANUP & RESET")
print("========================================\n")

# ========================================
# DELETE FILES (SCRAPER MÜLL)
# ========================================

FILES_TO_DELETE = [
    "scrapers/inspect_tesla_js.py",
    "scrapers/tesla_api_inspect.py",
    "scrapers/tesla_inspect.py",
    "scrapers/tesla_js_endpoints.py",
    "scrapers/tesla_network_inspect.py",
    "scrapers/tesla_state_inspect.py",
    "scrapers/scraper.py",
    "scrapers/providers/greenhouse_scraper.py",
    "tesla_careers_page.html",
    "tesla_resources.txt"
]

for file in FILES_TO_DELETE:
    if os.path.exists(file):
        os.remove(file)
        print(f"❌ gelöscht (file): {file}")
    else:
        print(f"⚪ nicht gefunden: {file}")

# ========================================
# DELETE DATA (TESLA + SPACEX RESET)
# ========================================

DATA_FOLDERS_TO_DELETE = [
    "data/tesla",
    "data/spacex"
]

for folder in DATA_FOLDERS_TO_DELETE:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"🔥 gelöscht (folder): {folder}")
    else:
        print(f"⚪ folder nicht gefunden: {folder}")

# ========================================
# RECREATE CLEAN DATA STRUCTURE
# ========================================

BASE_DATA_PATHS = [
    "data/tesla/raw",
    "data/tesla/processed",
    "data/tesla/exports",
    "data/spacex/raw",
    "data/spacex/processed",
    "data/spacex/exports"
]

for path in BASE_DATA_PATHS:
    os.makedirs(path, exist_ok=True)
    print(f"✅ erstellt: {path}")

# ========================================
# CREATE TESLA DETAILS MODULE
# ========================================

tesla_details_path = "scrapers/providers/tesla_details.py"

tesla_details_code = '''
def parse_tesla_details(driver):
    try:
        content_blocks = driver.find_elements("css selector", "div")

        best_text = ""

        for block in content_blocks:
            txt = block.text.strip()

            if len(txt) > 1000 and "Tesla homepage" not in txt:
                best_text = txt
                break

        if not best_text and content_blocks:
            best_text = content_blocks[0].text

        mission = ""
        requirements = ""

        if "What You'll Do" in best_text:
            parts = best_text.split("What You'll Do")
            if len(parts) > 1:
                mission = parts[1].split("What You'll Bring")[0][:1200]

        if "What You'll Bring" in best_text:
            parts = best_text.split("What You'll Bring")
            if len(parts) > 1:
                requirements = parts[1][:1200]

        if not mission:
            mission = best_text[:1200]

        if not requirements:
            requirements = best_text[:1200]

        return mission, requirements, ""

    except Exception as e:
        print("Tesla detail parsing error:", e)
        return "", "", ""
'''

if not os.path.exists(tesla_details_path):
    with open(tesla_details_path, "w", encoding="utf-8") as f:
        f.write(tesla_details_code.strip())
    print(f"✅ erstellt: {tesla_details_path}")
else:
    print(f"⚠️ existiert bereits: {tesla_details_path}")

print("\n========================================")
print("CLEANUP & RESET FERTIG")
print("========================================")
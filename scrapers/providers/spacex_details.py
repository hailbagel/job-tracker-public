import re


SECTION_NAMES = {
    "mission": (
        "about the job",
        "about this role",
        "responsibilities",
        "responsibility",
        "what you'll do",
        "what you will do",
        "description",
    ),
    "requirements": (
        "basic qualifications",
        "minimum qualifications",
        "qualifications",
        "requirements",
        "what you'll bring",
        "what you will bring",
    ),
    "benefits": (
        "benefits",
        "perks",
        "additional requirements",
    ),
}


def _clean_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def _section_key(line):
    normalized = re.sub(r"[^a-z0-9']+", " ", line.lower()).strip()
    if "benefit" in normalized and len(normalized) <= 60:
        return "benefits"

    for key, names in SECTION_NAMES.items():
        if any(normalized == name or normalized.startswith(name + " ") for name in names):
            return key
    return None


def parse_spacex_details(driver):
    try:
        body = driver.find_element("tag name", "body").text
        lines = _clean_lines(body)
        sections = {"mission": [], "requirements": [], "benefits": []}
        current = None

        for line in lines:
            section = _section_key(line)
            if section:
                current = section
                continue
            if current:
                sections[current].append(line)

        mission = "\n".join(sections["mission"][:80])[:1200]
        requirements = "\n".join(sections["requirements"][:80])[:1200]
        benefits = "\n".join(sections["benefits"][:80])[:1200]

        if not mission:
            mission = body[:1200]
        if not requirements:
            requirements = body[:1200]

        return mission, requirements, benefits

    except Exception as e:
        print("SpaceX detail parsing error:", e)
        return "", "", ""
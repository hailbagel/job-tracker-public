def parse_neura_details(driver):

    mission = ""
    requirements = ""
    benefits = ""

    try:
        sections = driver.find_elements("tag name", "section")

        for section in sections:
            text = section.text.lower()

            if "mission" in text:
                mission = section.text

            elif "requirement" in text:
                requirements = section.text

            elif "benefit" in text:
                benefits = section.text

    except Exception as e:
        print("Neura detail parsing error:", e)

    return mission, requirements, benefits
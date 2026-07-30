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
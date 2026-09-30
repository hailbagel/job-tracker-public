from selenium import webdriver


def create_edge_driver():
    """Create an Edge session that works on desktop and headless Linux hosts."""
    options = webdriver.EdgeOptions()

    for argument in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
    ):
        options.add_argument(argument)

    return webdriver.Edge(options=options)

class BaseScraper:

    def __init__(self, company):
        self.company = company

    def run(self):
        raise NotImplementedError("run() muss implementiert werden")

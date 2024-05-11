from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class Page:
    def __init__(self, url):
        self.driver = webdriver.Chrome()
        self.url = url

    def open(self):
        self.driver.get(self.url)

    def get_elements(self):
        return self.driver.find_elements(By.CSS_SELECTOR, '*')

    def quit(self):
        self.driver.quit()

class TestPage:
    def __init__(self, page):
        self.page = page

    def fetch_elements(self):
        return self.page.get_elements()

    def read_existing_elements(self):
        try:
            with open('elements.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def compare_and_log_elements(self, elements, existing_elements):
        new_elements = []
        for element in elements:
            xpath = element.get_attribute('xpath')
            logging.info(f'Testing element at {xpath}')  # Log the element being tested
            if not any(e['XPath'] == xpath for e in existing_elements):
                new_elements.append({"XPath": xpath})
        return new_elements

    def write_updates(self, existing_elements, new_elements):
        with open('elements.json', 'w') as file:
            json.dump(existing_elements + new_elements, file, indent=4)

    def test_elements(self):
        elements = self.fetch_elements()
        existing_elements = self.read_existing_elements()
        new_elements = self.compare_and_log_elements(elements, existing_elements)
        self.write_updates(existing_elements, new_elements)

def main():
    url = 'http://google.com'  # replace with your URL
    page = Page(url)
    test_page = TestPage(page)

    page.open()
    test_page.test_elements()
    page.quit()

if __name__ == "__main__":
    main()
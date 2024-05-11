from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw
import io
from selenium import webdriver
import datetime
import logging.config
import json

with open('./seleniumPageScraper/config/logging_config.json', 'r') as f:
    config = json.load(f)

logging.config.dictConfig(config)
logger = logging.getLogger()


class Page:
    def __init__(self, driver, url):
        self.driver = driver
        self.url = url

    def open(self):
        try:
            self.driver.get(self.url)
        except Exception as e:
            logger.error(f"Failed to open URL {self.url}. Error: {str(e)}")
            raise

    def get_screenshot(self):
        screenshot = self.driver.get_screenshot_as_png()
        return Image.open(io.BytesIO(screenshot))

    def get_elements(self):
        return self.driver.find_elements(By.CSS_SELECTOR, '*')

    def get_buttons(self):
        button_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button')
        input_button_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type=button], input[type=submit], input[type=reset]')
        return button_elements + input_button_elements

    def get_links(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'a')

    def get_text_boxes(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'input[type=text], textarea')

    def fetch_images(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'img')

    def fetch_checkboxes(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'input[type=checkbox]')

    def fetch_radio_buttons(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'input[type=radio]')

    def fetch_dropdowns(self):
        return self.driver.find_elements(By.CSS_SELECTOR, 'select')

    def click(self, element):
        element.click()

    def fill(self, element, text):
        element.clear()
        element.send_keys(text)


class TestPage:
    def __init__(self, page):
        self.page = page

    def get_xpath(self, element):
        def find_element_index(element):
            siblings = self.page.driver.execute_script('return arguments[0].parentNode.children;', element)
            for i, sibling in enumerate(siblings):
                if sibling == element:
                    return i + 1  # XPath is 1-indexed
            return None

        xpath = ''
        while element.tag_name != 'html':
            tag_name = element.tag_name
            index = find_element_index(element)
            xpath = f'/{tag_name}[{index}]' + xpath
            element = self.page.driver.execute_script('return arguments[0].parentNode;', element)

        return '/html' + xpath

    def get_css_selector(self, element):
        css_id = element.get_attribute('id')
        if css_id:
            return f'#{css_id}'
        else:
            class_names = element.get_attribute('class').split()
            if class_names:
                return '.' + '.'.join(class_names)
            else:
                return element.tag_name

    def fetch_elements(self):
        elements = {
            'button': self.page.get_buttons(),
            'link': self.page.get_links(),
            'text_box': self.page.get_text_boxes(),
            'image': self.page.fetch_images(),
            'checkbox': self.page.fetch_checkboxes(),
            'radio_button': self.page.fetch_radio_buttons(),
            'dropdown': self.page.fetch_dropdowns(),
        }
        return elements

    def read_existing_elements(self):
        try:
            with open('elements.json', 'r') as file:
                existing_elements = json.load(file)
                logger.info('Previous Elements loaded from elements.json')
        except FileNotFoundError:
            existing_elements = []
            logger.error('File elements.json not found. An new elements.json file will be created.')
        return existing_elements

    def compare_elements(self, elements, existing_elements):
        new_elements = []
        updates_occurred = False
        for element_type, elements in elements.items():
            for element in elements:
                if element.is_displayed():
                    xpath = self.get_xpath(element)
                    text = element.text
                    if not text:  # if text is empty
                        aria_label = element.get_attribute('aria-label')
                        if aria_label:  # if aria-label is available
                            text = aria_label
                    class_name = element.get_attribute('class')
                    logging.debug(f'Testing element: {element_type} named {text} at {xpath}')  # Log the element being tested

                    # Check if the element exists in the existing elements
                    matching_elements = [e for e in existing_elements if e['XPath'] == xpath]
                    if matching_elements:
                        changes = []
                        fields_to_check = {'Text': text, 'Class': class_name}
                        for field, new_value in fields_to_check.items():
                            old_value = matching_elements[0][field]
                            if old_value != new_value:
                                changes.append(f'Old {field}: {old_value}, New {field}: {new_value}')
                                matching_elements[0][field] = new_value
                        if changes:
                            matching_elements[0]['Timestamp'] = str(datetime.datetime.now())
                            updates_occurred = True
                            logging.info(f'Element {element_type} named {text} at {xpath} changed: ' + ', '.join(changes))
                        elif matching_elements[0]['Referenceable'] == 'No':
                            matching_elements[0]['Referenceable'] = 'Yes'
                            matching_elements[0]['Timestamp'] = str(datetime.datetime.now())
                            logging.info(f'Element {element_type} named {text} at {xpath} updated')
                        else:
                            logging.info(f'Element {element_type} {text} at {xpath} exists')
                    else:
                        logging.info(f'Element {element_type} named {text} at {xpath} added')
                        new_elements.append({
                            "Number": len(new_elements) + 1,
                            "Type": element_type,
                            "Name": element.get_attribute('name'),
                            "XPath": xpath,
                            "ID": element.get_attribute('id'),
                            "Class": class_name,
                            "Text": text,
                            "Referenceable": "Yes",
                            "Timestamp": str(datetime.datetime.now())
                        })
        return new_elements, updates_occurred

    def log_changes(self, updates_occurred):
        if updates_occurred:
            logging.info('Updates occurred during this run')

    def write_updates(self, existing_elements, new_elements):
        with open('elements.json', 'w') as file:
            json.dump(existing_elements + new_elements, file, indent=4)

    def test_elements(self):
        ## logging info to logs first time
        #logging.info('test_elements method started')
        elements = self.fetch_elements()
        existing_elements = self.read_existing_elements()
        new_elements, updates_occurred = self.compare_elements(elements, existing_elements)
        self.log_changes(updates_occurred)
        self.write_updates(existing_elements, new_elements)
        self.take_screenshot_and_highlight()
        logging.info('test_elements method finished')

    def teardown(self):
        self.page.driver.quit()

    def take_screenshot_and_highlight(self):
        # Take a screenshot
        screenshot = self.page.driver.get_screenshot_as_png()
        img = Image.open(io.BytesIO(screenshot))

        # Create a draw object
        draw = ImageDraw.Draw(img)

        # Find the elements and draw a box around each one
        for element in self.page.driver.find_elements(By.CSS_SELECTOR, '*'):
            if element.is_displayed():  # Only draw boxes around visible elements
                # Get the location and size of the element
                location = element.location
                size = element.size

                # Draw a box around the element
                top_left = (location['x'], location['y'])
                bottom_right = (location['x'] + size['width'], location['y'] + size['height'])
                draw.rectangle([top_left, bottom_right], outline='red')

        # Save the image
        img.save('screenshot.png')


def main():
    driver = webdriver.Chrome()  # replace with the path to your ChromeDriver
    url = 'http://google.com'  # replace with your URL

    page = Page(driver, url)
    test_page = TestPage(page)

    page.open()
    test_page.test_elements()
    test_page.teardown()


if __name__ == "__main__":
    main()

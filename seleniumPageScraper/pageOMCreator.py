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


from selenium.webdriver.common.by import By
from PIL import Image
import io
import logging

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
        elements = self.driver.find_elements(By.CSS_SELECTOR, '*')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def get_buttons(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'button, input[type=button], input[type=submit], input[type=reset]')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def get_links(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'a')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def get_text_boxes(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type=text], textarea')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def fetch_images(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'img')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def fetch_checkboxes(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type=checkbox]')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def fetch_radio_buttons(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[type=radio]')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def fetch_dropdowns(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'select')
        for element in elements:
            element.descriptive_name = self.get_descriptive_name(element)
        return elements

    def click(self, element):
        element.click()

    def fill(self, element, text):
        element.clear()
        element.send_keys(text)

    def get_descriptive_name(self, element):
        # Attempt to retrieve descriptive text from various attributes
        text = element.get_attribute('aria-label') or element.get_attribute('title')
        if not text:
            aria_labelledby = element.get_attribute('aria-labelledby')
            if aria_labelledby:
                ids = aria_labelledby.split()
                labels = [self.driver.find_element(By.ID, id).text for id in ids if self.driver.find_element(By.ID, id).text]
                text = ' '.join(labels)
        if not text:
            text = element.text
        if not text:
            text = self.driver.execute_script("return arguments[0].textContent.trim();", element)
        return text



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

    # TODO: Remove this method and replace with get_descriptive_name from Page class



    def compare_elements(self, elements, existing_elements):
        new_elements = []
        updates_occurred = False
        count = len(existing_elements)
        changes = []

        for element_type, elements in elements.items():
            for element in elements:
                if element.is_displayed():
                    xpath = self.get_xpath(element)
                    text = self.page.get_descriptive_name(element)
                    class_name = element.get_attribute('class')
                    element_name = element.get_attribute('name') if element.get_attribute('name') \
                        else self.page.get_descriptive_name(element)

                    # Match against existing elements in json using xpath; update if changes are detected
                    matching_elements = [e for e in existing_elements if e['XPath'] == xpath]
                    if matching_elements:
                        # Check if any key element attrib has changed
                        fields_to_check = {'Label': text, 'Class': class_name, 'XPath': xpath,
                                           'ID': element.get_attribute('id'), 'Name': element_name, 'Type': element_type,
                                           'Referenceable': 'Yes'}
                        for field, new_value in fields_to_check.items():
                            old_value = matching_elements[0][field]
                            if old_value != new_value:
                                changes.append(f'Old {field}: {old_value}, New {field}: {new_value}')
                                matching_elements[0][field] = new_value

                        if changes:  # If there are any changes, update the timestamp and log the changes
                            matching_elements[0]['Timestamp'] = str(datetime.datetime.now())
                            updates_occurred = True
                            logging.info(
                                f'Element #{matching_elements[0]['Number']} {element_type} named {text} \at {xpath} changed: ' + ', '.join(changes))
                        else:
                            logging.info(f'Element #{matching_elements[0]['Number']} {element_type} named {text} at {xpath} exists')
                    else:  # Add new element to json
                        count = count + 1
                        new_elements.append({
                            "Number": count,
                            "Type": element_type,
                            "Name": element_name,
                            "XPath": xpath,
                            "ID": element.get_attribute('id'),
                            "Class": class_name,
                            "Label": text,
                            "Referenceable": "Yes",
                            "Timestamp": str(datetime.datetime.now())
                        })
                        logging.info(f'New Element #{count} {element_type} named {text} at {xpath} found')
        if new_elements or updates_occurred:
            logging.info(f'Writing {len(new_elements)} new and {len(changes)} updates to elements.json')
            self.write_updates(existing_elements, new_elements)
        else:
            logging.info('No changes detected')
        return new_elements, updates_occurred

    def log_changes(self, updates_occurred):
        if updates_occurred:
            logging.info('Updates occurred during this run')

    def write_updates(self, existing_elements, new_elements):
        with open('elements.json', 'w') as file:
            json.dump(existing_elements + new_elements, file, indent=4)

    def test_elements(self):
        logging.info('Searching for elements on page ' + self.page.url)
        elements = self.fetch_elements()
        existing_elements = self.read_existing_elements()
        new_elements, updates_occurred = self.compare_elements(elements, existing_elements)
        self.log_changes(updates_occurred)
        self.take_screenshot_and_highlight()


    def teardown(self):
        self.page.driver.quit()

    def take_screenshot_and_highlight(self):
        # Take a screenshot
        screenshot = self.page.driver.get_screenshot_as_png()
        img = Image.open(io.BytesIO(screenshot))

        # Create a draw object
        draw = ImageDraw.Draw(img)

        # Find the elements and draw a box around each one
        # TODO: Need to find a better way to highlight and label elements
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

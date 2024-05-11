from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageDraw
import io

# Start the WebDriver
driver = webdriver.Firefox()  # or webdriver.Chrome()

# Open the webpage
driver.get('https://www.google.com')

# Take a screenshot
screenshot = driver.get_screenshot_as_png()
img = Image.open(io.BytesIO(screenshot))

# Create a draw object
draw = ImageDraw.Draw(img)

# Find the elements and draw a box around each one
for element in driver.find_elements(By.CSS_SELECTOR, '*'):
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

# Close the WebDriver
driver.quit()
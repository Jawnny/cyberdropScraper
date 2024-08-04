import os
import requests
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager

# Function to download images from a given album URL
def download_images_from_album(album_url, driver, base_download_dir):
    try:
        print(f"\nOpening album page: {album_url}")
        # Open the album page
        driver.get(album_url)

        # Explicitly wait for an element that ensures the page is fully loaded
        print("Waiting for the page to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "image-container"))
        )
        print("Page loaded successfully.")

        # Extract the album title from the h1 element with the specific class and title attribute
        album_title_element = driver.find_element(By.CSS_SELECTOR, "h1.title[title]")
        album_title = album_title_element.get_attribute("title")
        print(f"Album title found: {album_title}")

        # Create a directory for the current album using the album title
        album_folder_name = album_title.replace(" ", "_")  # Replace spaces with underscores for folder naming
        album_download_dir = os.path.join(base_download_dir, album_folder_name)
        os.makedirs(album_download_dir, exist_ok=True)

        # Find all 'a' tags with class 'image' to get href attributes
        print("Finding image page links...")
        image_links = driver.find_elements(By.CSS_SELECTOR, "a.image")

        if image_links:
            print(f"Found {len(image_links)} image page links.")
        else:
            print("No image page links found.")
            return

        # Store all image page URLs
        image_page_urls = [link.get_attribute('href') for link in image_links]

        for link_index, image_page_url in enumerate(image_page_urls):
            try:
                print(f"Accessing image page: {image_page_url}")

                # Open each image page with Selenium
                driver.get(image_page_url)

                # Wait for the specific image to be loaded by checking for an element that contains the image URL
                print("Waiting for the image to load...")
                time.sleep(2)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
                )
                print("Image page loaded.")

                # Get the page source after JavaScript execution
                image_page_source = driver.page_source

                # Use regex to find the first URL that matches the pattern in the rendered HTML content
                image_urls = re.findall(r'https://sunny\.cyberdrop\.ch/api/file/d/[^\s"]+', image_page_source)

                if image_urls:
                    print(f"Found image URL: {image_urls[0]}")
                    img_url = image_urls[0]  # Only process the first image URL

                    # Derive a unique name for the image based on the URL
                    parsed_url = urlparse(img_url)
                    image_name = os.path.basename(parsed_url.path)  # Use the path part of the URL for naming

                    # Download and save the image
                    image_response = requests.get(img_url, stream=True)
                    if image_response.status_code == 200:
                        image_path = os.path.join(album_download_dir, image_name + ".jpg")
                        with open(image_path, 'wb') as file:
                            for chunk in image_response.iter_content(1024):
                                file.write(chunk)
                        print(f"Downloaded: {image_name}")
                    else:
                        print(f"Failed to download image from {img_url}")
                else:
                    print("No image URLs found on the page.")

            except Exception as e:
                print(f"Error processing image link at index {link_index}: {e}")

    except Exception as e:
        print(f"Error opening album page {album_url}: {e}")

# Set up Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode (without opening a browser window)
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
chrome_options.add_argument('--log-level=3')  # Suppress logs
chrome_options.add_argument('--disable-logging')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument('--disable-infobars')

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Base directory to save downloaded images
base_download_dir = "downloaded_images"
os.makedirs(base_download_dir, exist_ok=True)

# Path to the text file containing URLs
url_file_path = "urls.txt"  # Replace with the actual path to your text file

# Open the text file and read URLs
with open(url_file_path, 'r') as url_file:
    album_urls = [line.strip() for line in url_file if line.strip()]

# Iterate over each URL in the file
for album_url in album_urls:
    download_images_from_album(album_url, driver, base_download_dir)

# Close the WebDriver
print("\nClosing the WebDriver.")
driver.quit()

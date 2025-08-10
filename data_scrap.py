from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import json
import time

# --------- CONFIG ---------
MAX_RESULTS = 20
BASE_URL = "https://www.booking.com"
# --------------------------

# Get today's and tomorrow's date
checkin_date = datetime.now().strftime("%Y-%m-%d")
checkout_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# Set up Chrome driver
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(), options=chrome_options)

try:
    # Directly open the search results page
    search_url = (
        f"{BASE_URL}/searchresults.html"
        f"?ss=United+States"
        f"&checkin={checkin_date}"
        f"&checkout={checkout_date}"
        f"&group_adults=2&no_rooms=1&group_children=0"
    )
    driver.get(search_url)

    # Wait for results to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='property-card']"))
    )

    properties = []
    cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card']")[:MAX_RESULTS]

    for card in cards:
        try:
            name = card.find_element(By.CSS_SELECTOR, "div[data-testid='title']").text.strip()
        except:
            name = None

        try:
            address = card.find_element(By.CSS_SELECTOR, "span[data-testid='address']").text.strip()
        except:
            address = None

        try:
            price_text = card.find_element(By.CSS_SELECTOR, "span[data-testid='price-and-discounted-price']").text
            base_price = float(price_text.replace("$", "").replace(",", "").split()[0])
        except:
            base_price = None

        try:
            img_elements = card.find_elements(By.CSS_SELECTOR, "img")
            images = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
        except:
            images = []

        try:
            star_elem = card.find_element(By.CSS_SELECTOR, "span[aria-label*='out of 5']")
            star_rating = int(star_elem.get_attribute("aria-label").split()[0])
        except:
            star_rating = None

        property_data = {
            "name": name,
            "description": None,  # Not on search page
            "address": address,
            "city": None,
            "country": "United States",
            "postal_code": None,
            "latitude": None,
            "longitude": None,
            "property_type": "hotel",
            "star_rating": star_rating,
            "total_rooms": None,
            "amenities": [],
            "facilities": [],
            "base_price": base_price,
            "currency": "USD",
            "supports_free_cancellation": "Free cancellation" in card.text,
            "supports_no_prepayment": "No prepayment" in card.text,
            "neighbourhood": None,
            "rooms": [
                {
                    "name": None,
                    "room_type": None,
                    "max_guests": None,
                    "size_sqm": None,
                    "room_amenities": [],
                    "base_price": base_price,
                    "genius_price": None,
                    "total_quantity": None,
                    "available_quantity": None,
                    "images": images
                }
            ]
        }

        properties.append(property_data)

    print(json.dumps(properties, indent=2))

finally:
    driver.quit()

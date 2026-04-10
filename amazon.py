import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------
# CONFIG
# ---------------------------------------
BASE_URL = "https://www.amazon.in/s?i=grocery&rh=n%3A2454178031"
OUTPUT_FILE = "amazon_grocery_main_categories.json"

# ---------------------------------------
# SETUP CHROME OPTIONS
# ---------------------------------------
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")

# Uncomment for headless mode later
# chrome_options.add_argument("--headless=new")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

wait = WebDriverWait(driver, 15)

# ---------------------------------------
# OPEN PAGE
# ---------------------------------------
print("Opening Amazon Grocery page...")
driver.get(BASE_URL)

# Wait for category section to load
wait.until(
    EC.presence_of_element_located((By.ID, "n-title"))
)

time.sleep(2)  # small delay for safety

# ---------------------------------------
# EXTRACT CATEGORY LINKS
# ---------------------------------------
category_elements = driver.find_elements(
    By.CSS_SELECTOR,
    "li.apb-browse-refinements-indent-2 a.a-link-normal"
)

categories = []

for element in category_elements:
    name = element.text.strip()
    link = element.get_attribute("href")

    if name and link:
        categories.append({
            "main_category": "Grocery & Gourmet Foods",
            "subcategory_name": name,
            "subcategory_url": link
        })

print(f"Found {len(categories)} subcategories")

# ---------------------------------------
# SAVE TO JSON
# ---------------------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(categories, f, indent=2, ensure_ascii=False)

print("Saved to JSON successfully ✅")

driver.quit()
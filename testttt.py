from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

url = "https://www.amazon.in/dp/B0B1D5SP8W"

driver = webdriver.Chrome()
driver.get(url)

wait = WebDriverWait(driver, 10)

# Wait for page
wait.until(EC.presence_of_element_located((By.ID, "voyagerNorthstarATF")))

data = {}

# ==========================
# 🔹 1. ABOUT THIS ITEM (BULLETS)
# ==========================
about_items = []

try:
    bullets = driver.find_elements(By.CSS_SELECTOR, "#feature-bullets ul li span.a-list-item")
    for b in bullets:
        text = b.text.strip()
        if text:
            about_items.append(text)
except:
    print("⚠️ About section not found")

data["about"] = about_items


# ==========================
# 🔹 2. CLICK "Item details"
# ==========================
try:
    item_btn = driver.find_element(By.XPATH, "//span[text()='Item details']")
    driver.execute_script("arguments[0].click();", item_btn)
    time.sleep(2)
except:
    print("⚠️ Could not click Item details")


# ==========================
# 🔹 3. ITEM DETAILS
# ==========================
item_details = {}

rows = driver.find_elements(By.CSS_SELECTOR, "#item_details tr")

for row in rows:
    try:
        key = row.find_element(By.TAG_NAME, "th").text
        value = row.find_element(By.TAG_NAME, "td").text
        item_details[key] = value
    except:
        continue

data["item_details"] = item_details


# ==========================
# 🔹 4. CLICK "Measurements"
# ==========================
try:
    measure_btn = driver.find_element(By.XPATH, "//span[text()='Measurements']")
    driver.execute_script("arguments[0].click();", measure_btn)
    time.sleep(2)
except:
    print("⚠️ Could not click Measurements")


# ==========================
# 🔹 5. MEASUREMENTS
# ==========================
measurements = {}

rows = driver.find_elements(By.CSS_SELECTOR, "#measurements tr")

for row in rows:
    try:
        key = row.find_element(By.TAG_NAME, "th").text
        value = row.find_element(By.TAG_NAME, "td").text
        measurements[key] = value
    except:
        continue

data["measurements"] = measurements


# ==========================
# 🔹 FINAL OUTPUT
# ==========================
print("\n✅ ABOUT THIS ITEM:")
for i in data["about"]:
    print("-", i)

print("\n✅ ITEM DETAILS:")
for k, v in data["item_details"].items():
    print(f"{k}: {v}")

print("\n✅ MEASUREMENTS:")
for k, v in data["measurements"].items():
    print(f"{k}: {v}")

driver.quit()
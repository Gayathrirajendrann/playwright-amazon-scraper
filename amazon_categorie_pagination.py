import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# ---------- LOAD INPUT JSON ----------

with open("amazon_grocery_main_categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)


# ---------- SETUP SELENIUM ----------

chrome_options = Options()
chrome_options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)


results = []


# ---------- LOOP THROUGH CATEGORY URLS ----------

for item in categories:

    category_name = item["subcategory_name"]
    url = item["subcategory_url"]

    print(f"\nProcessing: {category_name}")

    driver.get(url)
    time.sleep(3)

    try:

        # ---------- STEP 1: GET SEE ALL URL ----------

        see_all = driver.find_element(By.ID, "apb-desktop-browse-search-see-all")
        see_all_url = see_all.get_attribute("href")

        print("See All URL:", see_all_url)

    except:

        print("See all results button not found")
        continue


    # ---------- STEP 2: OPEN SEE ALL PAGE ----------

    driver.get(see_all_url)
    time.sleep(3)


    # ---------- STEP 3: FIND PAGINATION ----------

    try:

        pagination_items = driver.find_elements(By.CSS_SELECTOR, ".s-pagination-item")

        last_page = 1

        for item_page in pagination_items:

            text = item_page.text.strip()

            if text.isdigit():

                page_num = int(text)

                if page_num > last_page:
                    last_page = page_num


        print("Total Pages:", last_page)


    except:

        print("Pagination not found")
        last_page = 1


    # ---------- SAVE RESULT ----------

    results.append({

        "category": category_name,
        "see_all_url": see_all_url,
        "total_pages": last_page

    })


# ---------- SAVE OUTPUT ----------

with open("category_pagination.json", "w", encoding="utf-8") as f:

    json.dump(results, f, indent=4)


driver.quit()

print("\nFinished collecting pagination info.")
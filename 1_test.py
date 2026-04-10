from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import random
import os

INPUT_FILE = "product_urls.json"
OUTPUT_FILE = "output.json"
FAILED_FILE = "failed.json"
PROGRESS_FILE = "progress.txt"

# -------------------------
# Load input
# -------------------------
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

# Remove duplicates
seen = set()
unique_products = []

for p in products:
    if p["url"] not in seen:
        seen.add(p["url"])
        unique_products.append(p)

print(f"Total unique URLs: {len(unique_products)}")

# -------------------------
# Resume support
# -------------------------
start_index = 0
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        start_index = int(f.read().strip())
        print(f"Resuming from index: {start_index}")

# -------------------------
# Load previous outputs
# -------------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

all_data = load_json(OUTPUT_FILE)
failed_data = load_json(FAILED_FILE)

failed_urls_set = {f["url"] for f in failed_data}

# -------------------------
# Playwright Scraper
# -------------------------
def scrape_amazon_playwright(page, url):
    page.goto(url, timeout=60000)

    # wait for content
    page.wait_for_timeout(random.randint(3000, 5000))

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    result = {}

    # -------------------------
    # Top Highlights
    # -------------------------
    rows = soup.select("#topHighlight table tr")
    for row in rows:
        key = row.select_one("td:first-child span")
        value = row.select_one("td:last-child span")

        if key and value:
            result[key.get_text(strip=True)] = value.get_text(strip=True)

    # -------------------------
    # About This Item
    # -------------------------
    bullets = soup.select("#feature-bullets li span.a-list-item")
    if not bullets:
        bullets = soup.select("#feature-bullets li")

    result["about_this_item"] = [
        b.get_text(strip=True) for b in bullets if b.get_text(strip=True)
    ]

    # -------------------------
    # Diet Info
    # -------------------------
    vnv = soup.select_one("#vnv-container .vnv-text")
    if vnv:
        result["diet_info"] = " ".join(vnv.get_text(strip=True).split())

    # -------------------------
    # Product Description
    # -------------------------
    desc = soup.select_one("#productDescription")

    if not desc:
        desc = soup.select_one("#productDescription_feature_div")

    if not desc:
        desc = soup.select_one("#aplus")

    if desc:
        result["product_description"] = desc.get_text(" ", strip=True)

    return result

# -------------------------
# Retry Logic (2 retries)
# -------------------------
def scrape_with_retry(page, url, retries=2):
    for attempt in range(retries):
        try:
            data = scrape_amazon_playwright(page, url)

            if data.get("product_description") or data.get("about_this_item"):
                return data

            print(f"⚠️ Partial data → Retry {attempt+1}")
            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"⚠️ Error → Retry {attempt+1}: {e}")
            time.sleep(random.uniform(5, 8))

    return {}

# -------------------------
# Empty check
# -------------------------
def is_empty(data):
    return not (data.get("about_this_item") or data.get("product_description"))

# -------------------------
# Main Loop (Playwright)
# -------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # keep False for stability
    page = browser.new_page()

    for i in range(start_index, len(unique_products)):
        product = unique_products[i]
        url = product["url"]
        asin = product["asin"]

        print(f"[{i}] Scraping: {asin}")

        try:
            data = scrape_with_retry(page, url)

            # attach metadata
            data["asin"] = asin
            data["url"] = url

            # -------------------------
            # Handle empty data
            # -------------------------
            if is_empty(data):
                print("⚠️ Empty data — adding to failed")

                if url not in failed_urls_set:
                    failed_data.append({"asin": asin, "url": url})
                    failed_urls_set.add(url)

                    with open(FAILED_FILE, "w", encoding="utf-8") as f:
                        json.dump(failed_data, f, indent=4, ensure_ascii=False)

            else:
                all_data.append(data)

                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(all_data, f, indent=4, ensure_ascii=False)

            # -------------------------
            # Save progress
            # -------------------------
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(i + 1))

            # -------------------------
            # Delay (IMPORTANT)
            # -------------------------
            sleep_time = random.uniform(3, 6)
            print(f"Sleeping {sleep_time:.2f} sec...\n")
            time.sleep(sleep_time)

        except Exception as e:
            print(f"❌ Error at {asin}: {e}")

            if url not in failed_urls_set:
                failed_data.append({"asin": asin, "url": url})
                failed_urls_set.add(url)

                with open(FAILED_FILE, "w", encoding="utf-8") as f:
                    json.dump(failed_data, f, indent=4, ensure_ascii=False)

            time.sleep(5)
            continue

    browser.close()

print("✅ Scraping completed!")
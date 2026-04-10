from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import random

def scrape_amazon_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # keep False for debugging
        page = browser.new_page()

        print("Opening URL...")
        page.goto(url, timeout=60000)

        # wait for page to fully load
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
        # Product Description
        # -------------------------
        desc = soup.select_one("#productDescription")

        if not desc:
            desc = soup.select_one("#productDescription_feature_div")

        if desc:
            result["product_description"] = desc.get_text(" ", strip=True)

        browser.close()
        return result


# -------------------------
# TEST URL
# -------------------------
url = "https://www.amazon.in/Prolicious-Protein-Khakhra-Flavourful-170grams/dp/B0F3X6G2ZG/ref=sr_1_72"  # change to any URL

data = scrape_amazon_playwright(url)

# -------------------------
# PRINT RESULT
# -------------------------
print("\n✅ SCRAPED DATA:\n")
print(json.dumps(data, indent=4, ensure_ascii=False))
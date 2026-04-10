import json
import os
import re
import random
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==========================
# FILES
# ==========================

INPUT_FILE = "urls.json"
OUTPUT_FILE = "product_data.json"
PROGRESS_FILE = "progress_product.json"
FAILED_FILE = "failed_products.json"

# ==========================
# BROWSER SETUP
# ==========================

def create_driver():
    options = Options()

    # ── Anti-detection flags ──────────────────────────────────────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ── Window & language ─────────────────────────────────────────────────
    options.add_argument("--window-size=1440,900")
    options.add_argument("--lang=en-US")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # ── Realistic user agent ──────────────────────────────────────────────
    ua = random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ])
    options.add_argument(f"--user-agent={ua}")

    # ── OPTIONAL: Run headless (comment out to see browser) ───────────────
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    # ── Patch navigator.webdriver to undefined ────────────────────────────
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """
    })

    return driver

# ==========================
# CAPTCHA / BLOCK DETECTION
# ==========================

def is_blocked(driver):
    title = driver.title.lower()
    src = driver.page_source.lower()
    return (
        "captcha" in title
        or "robot check" in title
        or "captcha" in src
        or "enter the characters you see below" in src
        or "automated access" in src
        or len(driver.page_source) < 5000
    )

# ==========================
# SAFE TEXT HELPER
# ==========================

def safe_text(driver, by, selector, default=None):
    try:
        el = driver.find_element(by, selector)
        return el.text.strip() or default
    except NoSuchElementException:
        return default

def safe_attr(driver, by, selector, attr, default=None):
    try:
        el = driver.find_element(by, selector)
        return el.get_attribute(attr) or default
    except NoSuchElementException:
        return default

def clean(text):
    return re.sub(r'\s+', ' ', text).strip() if text else None

# ==========================
# HUMAN-LIKE SCROLL
# ==========================

def human_scroll(driver):
    """Scroll down slowly like a human to trigger lazy-loaded content."""
    total_height = driver.execute_script("return document.body.scrollHeight")
    current = 0
    step = random.randint(300, 600)
    while current < total_height:
        current += step
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.1, 0.3))

# ==========================
# SCRAPE ONE PRODUCT
# ==========================

def scrape_product(driver, asin):
    url = f"https://www.amazon.in/dp/{asin}"

    for attempt in range(3):
        try:
            driver.get(url)

            # Wait for page body
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            if is_blocked(driver):
                wait = 60 + (attempt * 45)
                print(f"  ⚠ Blocked/Captcha (attempt {attempt+1}) → sleeping {wait}s")
                time.sleep(wait)
                continue

            # Scroll to load lazy content
            human_scroll(driver)
            time.sleep(random.uniform(1.0, 2.0))

            # ── 1. TITLE ──────────────────────────────────────────────────
            title = safe_text(driver, By.ID, "productTitle")

            # Validate page loaded properly
            if not title:
                print(f"  ⚠ Title missing (attempt {attempt+1}) — retrying")
                time.sleep(15)
                continue

            # ── 2. BRAND ──────────────────────────────────────────────────
            brand = None
            for sel in ["#bylineInfo", "#brand"]:
                try:
                    brand = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                    if brand:
                        break
                except NoSuchElementException:
                    pass

            # ── 3. PRICE ──────────────────────────────────────────────────
            price = None
            price_selectors = [
                ".a-price .a-offscreen",
                "#priceblock_ourprice",
                "#priceblock_dealprice",
                "#price_inside_buybox",
                ".apexPriceToPay .a-offscreen",
                ".reinventPricePriceToPayMargin .a-offscreen",
            ]
            for sel in price_selectors:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    val = el.get_attribute("innerHTML").strip()
                    if val:
                        price = clean(val)
                        break
                except NoSuchElementException:
                    pass

            # ── 4. RATING & REVIEWS ───────────────────────────────────────
            rating = None
            try:
                el = driver.find_element(By.ID, "acrPopover")
                rating = clean(el.get_attribute("title") or el.text)
            except NoSuchElementException:
                pass

            review_count = safe_text(driver, By.ID, "acrCustomerReviewText")

            # ── 5. AVAILABILITY ───────────────────────────────────────────
            availability = None
            try:
                el = driver.find_element(By.CSS_SELECTOR, "#availability span")
                availability = clean(el.text)
            except NoSuchElementException:
                pass

            # ── 6. TOP HIGHLIGHTS (po-* rows) ─────────────────────────────
            top_highlights = {}
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "tr[class*='po-']")
                for row in rows:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 2:
                        key = clean(tds[0].text)
                        val = clean(tds[1].text)
                        if key and val:
                            top_highlights[key] = val
            except Exception:
                pass

            # ── 7. FEATURE BULLETS ────────────────────────────────────────
            bullets = []
            try:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#feature-bullets ul li span.a-list-item"
                )
                for item in items:
                    text = clean(item.text)
                    if text and text.lower() not in ("show more", "show less", ""):
                        bullets.append(text)
            except Exception:
                pass

            # ── 8. PRODUCT DESCRIPTION ────────────────────────────────────
            description = None
            try:
                el = driver.find_element(By.ID, "productDescription")
                description = clean(el.text)
            except NoSuchElementException:
                pass

            # ── 9. TECHNICAL DETAILS TABLES ───────────────────────────────
            tech_details = {}
            table_selectors = [
                "#productDetails_techSpec_section_1 tr",
                "#productDetails_techSpec_section_2 tr",
                "#productDetails_db_sections tr",
                "#prodDetails tr",
                ".prodDetTable tr",
            ]
            for sel in table_selectors:
                try:
                    rows = driver.find_elements(By.CSS_SELECTOR, sel)
                    for row in rows:
                        try:
                            th = row.find_element(By.TAG_NAME, "th")
                            td = row.find_element(By.TAG_NAME, "td")
                            key = clean(th.text)
                            val = clean(td.text)
                            if key and val:
                                tech_details[key] = val
                        except NoSuchElementException:
                            pass
                except Exception:
                    pass

            # ── 10. DETAIL BULLETS (older layout) ─────────────────────────
            detail_bullets_attrs = {}
            try:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#detailBullets_feature_div li"
                )
                for item in items:
                    spans = item.find_elements(By.CSS_SELECTOR, "span span")
                    if len(spans) >= 2:
                        key = clean(
                            spans[0].text
                            .rstrip(":")
                            .rstrip("\u200f")
                            .rstrip("\u00a0")
                        )
                        val = clean(spans[1].text)
                        if key and val:
                            detail_bullets_attrs[key] = val
            except Exception:
                pass

            # ── 11. A+ CONTENT ────────────────────────────────────────────
            aplus_text = []
            try:
                els = driver.find_elements(
                    By.CSS_SELECTOR,
                    "#aplus p, #aplus h1, #aplus h2, #aplus h3, "
                    "#aplusBrandStory_feature_div p"
                )
                for el in els:
                    text = clean(el.text)
                    if text:
                        aplus_text.append(text)
            except Exception:
                pass

            # ── 12. MAIN IMAGE ────────────────────────────────────────────
            images = []
            for sel in ["#landingImage", "#imgTagWrapperId img"]:
                try:
                    img = driver.find_element(By.CSS_SELECTOR, sel)
                    src = (
                        img.get_attribute("data-old-hires")
                        or img.get_attribute("src")
                    )
                    if src and src.startswith("http"):
                        images.append(src)
                    break
                except NoSuchElementException:
                    pass

            # ── 13. MERGE ATTRIBUTES ──────────────────────────────────────
            merged = {}
            merged.update(top_highlights)
            merged.update(detail_bullets_attrs)
            merged.update(tech_details)

            return {
                "asin": asin,
                "url": url,
                "title": title,
                "brand": brand,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "availability": availability,
                "top_highlights": top_highlights,
                "bullets": bullets,
                "description": description,
                "attributes": merged,
                "aplus_content": aplus_text,
                "images": images,
                "scraped_at": datetime.now().isoformat(),
            }

        except TimeoutException:
            print(f"  ⏱ Timeout on attempt {attempt+1}")
            time.sleep(15)
        except Exception as e:
            print(f"  ❌ Error on attempt {attempt+1}: {e}")
            time.sleep(10)

    return None

# ==========================
# LOAD DATA
# ==========================

with open(INPUT_FILE, encoding="utf-8") as f:
    all_products = json.load(f)

if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            content = f.read().strip()
            scraped_data = json.loads(content) if content else []
    except json.JSONDecodeError:
        print("⚠ product_data.json corrupted — starting fresh")
        scraped_data = []
else:
    scraped_data = []

existing_asins = {p["asin"] for p in scraped_data}

# ==========================
# LOAD PROGRESS
# ==========================

if os.path.exists(PROGRESS_FILE):
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            content = f.read().strip()
            progress = json.loads(content) if content else {}
        start_index = progress.get("index", -1) + 1
    except json.JSONDecodeError:
        start_index = 0
else:
    start_index = 0

print(f"📦 Total URLs : {len(all_products)}")
print(f"✅ Already done: {len(existing_asins)}")
print(f"▶  Starting at : index {start_index}")

# ==========================
# MAIN LOOP
# ==========================

driver = create_driver()
failed = []
consecutive_failures = 0

try:
    for i in range(start_index, len(all_products)):

        item = all_products[i]
        asin = item["asin"]
        url  = item["url"]

        print(f"\n[{i+1}/{len(all_products)}] ASIN: {asin}")

        if asin in existing_asins:
            print("  ⏭ Already scraped → skipping")
            continue

        result = scrape_product(driver, asin)

        if result is None:
            print("  ❌ Failed after all retries")
            failed.append({"asin": asin, "url": url})
            consecutive_failures += 1

            # After 5 consecutive failures restart the browser
            if consecutive_failures >= 5:
                print(f"\n  🛑 {consecutive_failures} consecutive failures — restarting browser + 3 min pause")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(180)
                driver = create_driver()
                consecutive_failures = 0
            continue

        consecutive_failures = 0
        scraped_data.append(result)
        existing_asins.add(asin)

        print(f"  ✅ {(result['title'] or 'No Title')[:70]}")
        if result["price"]:
            print(f"     Price      : {result['price']}")
        if result["top_highlights"]:
            print(f"     Highlights : {list(result['top_highlights'].keys())}")
        if result["attributes"]:
            print(f"     Attributes : {len(result['attributes'])} keys")

        # ── SAVE ──────────────────────────────────────────────────────────
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)

        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"index": i}, f)

        # ── DELAY ─────────────────────────────────────────────────────────
        if (i + 1) % 50 == 0:
            long_break = random.uniform(45, 90)
            print(f"  ☕ 50-product break: {long_break:.0f}s")
            time.sleep(long_break)
        else:
            time.sleep(random.uniform(3, 7))

finally:
    driver.quit()
    print("  🔒 Browser closed")

# ==========================
# SAVE FAILED
# ==========================

with open(FAILED_FILE, "w", encoding="utf-8") as f:
    json.dump(failed, f, indent=2)

print(f"\n🎉 Done — {len(scraped_data)} saved, {len(failed)} failed.")
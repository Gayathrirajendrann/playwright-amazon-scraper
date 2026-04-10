import requests
from bs4 import BeautifulSoup
import json
import random
import time
import os

# ==========================
# CONFIG
# ==========================

BASE_URL ="https://www.amazon.in/s?i=grocery&rh=n%3A4859493031&s=popularity-rank&fs=true"

TOTAL_PAGES = 338
BASE_DOMAIN = "https://www.amazon.in"

PRODUCT_FILE = "product_urls.json"
PROGRESS_FILE = "progress.json"
FAILED_FILE = "failed_pages.json"
PROXY_FILE = "proxies.txt"


# ==========================
# LOAD PROXIES
# ==========================

# def load_proxies():
#     if os.path.exists(PROXY_FILE):
#         with open(PROXY_FILE) as f:
#             return [p.strip() for p in f.readlines()]
#     return []

# PROXIES = load_proxies()


# def get_proxy():
#     if not PROXIES:
#         return None
#     proxy = random.choice(PROXIES)
#     return {"http": proxy, "https": proxy}


# ==========================
# USER AGENTS
# ==========================

USER_AGENTS = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/119 Safari/537.36",
"Mozilla/5.0 (X11; Linux x86_64) Firefox/120"
]


def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    }


# ==========================
# LOAD EXISTING DATA
# ==========================
if os.path.exists(PRODUCT_FILE):
    with open(PRODUCT_FILE) as f:
        products = json.load(f)
else:
    products = []

existing_asins = {p["asin"] for p in products}


# ==========================
# LOAD PROGRESS
# ==========================

if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)
    start_page = progress["page"] + 1
else:
    start_page = 1


# ==========================
# CAPTCHA DETECTION
# ==========================

def detect_captcha(html):

    if "captcha" in html.lower():
        return True

    if "Enter the characters you see below" in html:
        return True

    return False


# ==========================
# SCRAPE PAGE
# ==========================

def scrape_page(url):

    for attempt in range(2):

        try:

           # proxy = get_proxy()

            response = requests.get(
                url,
                headers=headers(),
                #   proxies=proxy,
                timeout=30
            )

            html = response.text

            if detect_captcha(html):

                print("Captcha detected - sleeping")
                time.sleep(30)
                continue

            soup = BeautifulSoup(html, "html.parser")

            results = soup.select('div[data-component-type="s-search-result"]')

            page_products = []
            duplicate_count = 0
            new_count = 0
            for r in results:

                asin = r.get("data-asin")

                if not asin:
                    continue

                if asin in existing_asins:
                    duplicate_count += 1
                    continue

                link = r.select_one("a.a-link-normal")

                if link:

                    href = link.get("href")

                    if href:

                        url = BASE_DOMAIN + href.split("?")[0]

                        page_products.append({
                            "asin": asin,
                            "url": url
                        })

                        existing_asins.add(asin)
                        new_count += 1
            print("New products:", new_count)
            print("Already exists:", duplicate_count)
            return page_products

        except Exception as e:

            print("Retry", attempt+1)
            time.sleep(5)

    return None


# ==========================
# MAIN LOOP
# ==========================

failed_pages = []

for page in range(start_page, TOTAL_PAGES+1):
#&page=3&qid=1772898607&xpid=jAnERY6QdoUqZ&ref=sr_pg_3
    page_url = f"{BASE_URL}&page={page}"

    print("\nScraping page:", page)

    page_products = scrape_page(page_url)

    if page_products is None:

        print("Page failed")
        failed_pages.append(page_url)
        continue

    products.extend(page_products)

    print("Products found:", len(page_products))

    # SAVE PRODUCT DATA
    with open(PRODUCT_FILE,"w") as f:
        json.dump(products,f,indent=2)

    # SAVE PROGRESS
    with open(PROGRESS_FILE,"w") as f:
        json.dump({"page":page},f)

    # RANDOM DELAY
    delay = random.randint(4,8)

    print("Waiting",delay,"seconds")

    time.sleep(delay)


# SAVE FAILED PAGES
with open(FAILED_FILE,"w") as f:
    json.dump(failed_pages,f,indent=2)

print("\nScraping Finished")
import requests
from bs4 import BeautifulSoup

url = "https://www.amazon.in/Karachi-Bakery-Karachibakery-Oats-250gram/dp/B0CP24VWFF/ref=sr_1_85"  # 👈 replace with your failed URL

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.amazon.in/"
}

session = requests.Session()

print("Fetching URL...\n")

response = session.get(url, headers=headers, timeout=15)

print("Status Code:", response.status_code)
print("Final URL:", response.url)

html = response.text

# -------------------------
# Save HTML for inspection
# -------------------------
with open("debug.html", "w", encoding="utf-8") as f:
    f.write(html)

print("HTML saved as debug.html\n")

# -------------------------
# Basic checks
# -------------------------
html_lower = html.lower()

if "captcha" in html_lower:
    print("🔴 CAPTCHA detected → Amazon blocked request")

elif "api-services-support@amazon.com" in html_lower:
    print("🔴 BLOCKED by Amazon (bot detection)")

elif "sorry, we just need to make sure you're not a robot" in html_lower:
    print("🔴 Robot check page")

elif "currently unavailable" in html_lower:
    print("🟡 Product unavailable")

else:
    print("🟢 No obvious blocking detected")

# -------------------------
# Parse HTML
# -------------------------
soup = BeautifulSoup(html, "html.parser")

# -------------------------
# Check selectors
# -------------------------
print("\n🔍 Checking elements...\n")

top_highlight = soup.select_one("#topHighlight")
feature_bullets = soup.select("#feature-bullets li")
product_desc = soup.select_one("#productDescription")

print("Top Highlight found:", bool(top_highlight))
print("Feature bullets found:", len(feature_bullets))
print("Product description found:", bool(product_desc))

# -------------------------
# Print sample extracted data
# -------------------------
if feature_bullets:
    print("\nSample bullet:")
    print(feature_bullets[0].get_text(strip=True))

if product_desc:
    print("\nProduct description:")
    print(product_desc.get_text(strip=True)[:300])

# -------------------------
# Final diagnosis
# -------------------------
print("\n🧠 Diagnosis:")

if not top_highlight and not feature_bullets and not product_desc:
    print("➡️ Likely BLOCKED or DIFFERENT PAGE STRUCTURE")

elif not feature_bullets:
    print("➡️ Missing 'About this item' (different layout)")

elif not product_desc:
    print("➡️ No product description present")

else:
    print("➡️ Page looks normal — issue may be intermittent")
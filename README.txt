# 🛒 Amazon Product Scraper (Playwright + BeautifulSoup)

A robust Amazon scraper built using **Playwright** and **BeautifulSoup** to extract product details while handling anti-bot mechanisms.

---
# Architecture

```
product_urls.json
        │
        ▼
Preprocessing
(remove duplicates + resume)
        │
        ▼
Scraper (Playwright)
        │
        ▼
Parser (BeautifulSoup)
        │
   ┌────┴────┐
   ▼         ▼
Output     Failed
        │
        ▼
Progress Tracker
```

---
## 🚀 Features

- ✅ Scrapes 1000+ product URLs  
- 🔁 Retry mechanism  
- 🔄 Auto-resume after crash  
- 🧹 Duplicate URL removal  
- ❌ Failure tracking (`failed.json`)  
- ⏱️ Human-like delays  
- 🛡️ Works even when blocked  

---

## 📂 Project Structure

```
amazon-scraper/
│
├── product_urls.json
├── output.json
├── failed.json
├── progress.txt
├── scraper.py
└── README.md
```

---

## ⚙️ How It Works

1. Load URLs  
2. Remove duplicates  
3. Resume progress  
4. Scrape using Playwright  
5. Parse using BeautifulSoup  
6. Save output & failures  

---

## 🔁 Retry Logic

- Retries each URL 2 times  
- Marks failed if still unsuccessful  

---

## 🛡️ Anti-Bot Handling

- Real browser (Playwright)  
- Random delays (3–6 sec)  
- Headful mode  

---

## ⚠️ Notes

👉 30–40% empty data is normal due to:
- Missing descriptions  
- CAPTCHA  
- Lazy loading  
- Region differences  

---

## 🧪 Debugging

```python
with open("debug.html", "w", encoding="utf-8") as f:
    f.write(page.content())
```

---

## ▶️ Run

```bash
pip install playwright beautifulsoup4
playwright install
python scraper.py
```

---

## ⚠️ Disclaimer

Educational use only. Scraping Amazon may violate their Terms.

import os
import time
import random
import csv
import pickle
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SEARCH_QUERY = "software developer"
SEARCH_LOCATION = "remote"
URL = f"https://www.indeed.com/jobs?q={SEARCH_QUERY}&l={SEARCH_LOCATION}&start="
MAX_NEW = 10
RESULTS_PER_PAGE = 10
SCRAPED_FILE = "scraped_jobs.txt"
OUTPUT_CSV = "jobs.csv"
COOKIE_FILE = "cookies.pkl"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

# ─── HELPERS ────────────────────────────────────────────────────────────────────


def init_driver():
    opts = uc.ChromeOptions()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    driver = uc.Chrome(options=opts)
    return driver


def save_cookies(driver, path):
    with open(path, "wb") as f:
        pickle.dump(driver.get_cookies(), f)


def load_cookies(driver, path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)


def load_scraped_urls():
    if not os.path.exists(SCRAPED_FILE):
        return set()
    with open(SCRAPED_FILE) as f:
        return set(line.strip() for line in f)


def save_job_url(url):
    with open(SCRAPED_FILE, "a") as f:
        f.write(url + "\n")


def ensure_csv_header():
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["title", "company", "url", "description"])


def append_job(title, company, url, desc):
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([title, company, url, desc])

# ─── MAIN ───────────────────────────────────────────────────────────────────────


def main():
    scraped = load_scraped_urls()
    ensure_csv_header()
    new_count = 0
    page = 0

    driver = init_driver()
    driver.get("https://www.indeed.com/")

    if not os.path.exists(COOKIE_FILE):
        print("\n🚨 Please solve CAPTCHA manually if it appears.")
        print("🔐 After solving, press ENTER here to save cookies and continue...")
        input()
        save_cookies(driver, COOKIE_FILE)
    else:
        driver.get("https://www.indeed.com/")
        load_cookies(driver, COOKIE_FILE)
        driver.refresh()

    while new_count < MAX_NEW:
        start = page * RESULTS_PER_PAGE
        driver.get(f"{URL}{start}")

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.tapItem"))
            )
        except:
            print("❌ No job cards found; stopping.")
            break

        time.sleep(random.uniform(1.5, 3))
        cards = driver.find_elements(By.CSS_SELECTOR, "a.tapItem")
        for card in cards:
            if new_count >= MAX_NEW:
                break

            jk = card.get_attribute("data-jk")
            if not jk:
                continue
            job_url = f"https://www.indeed.com/viewjob?jk={jk}"
            if job_url in scraped:
                continue

            title = card.get_attribute("aria-label") or card.text.strip()
            try:
                company = card.find_element(
                    By.CSS_SELECTOR, "span.companyName").text.strip()
            except:
                company = ""

            driver.get(job_url)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.ID, "jobDescriptionText"))
                )
            except:
                driver.back()
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")
            desc_div = soup.find("div", id="jobDescriptionText")
            if not desc_div or "remote" not in desc_div.get_text().lower():
                driver.back()
                continue

            description = desc_div.get_text("\n", strip=True)
            append_job(title, company, job_url, description)
            save_job_url(job_url)
            scraped.add(job_url)
            new_count += 1
            print(f"[{new_count}/{MAX_NEW}] {title} @ {company}")

            time.sleep(random.uniform(2, 4))
            driver.back()
            time.sleep(random.uniform(1, 2))

        page += 1
        time.sleep(random.uniform(3, 5))

    print(f"\n✅ Done: scraped {new_count} new remote jobs.")
    driver.quit()


if __name__ == "__main__":
    main()

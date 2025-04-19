import os
import time
import random
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium_stealth import stealth

# ─── CONFIG ────────────────────────────────────────────────────────────────────
SEARCH_QUERY = "software developer"
SEARCH_LOCATION = "remote"
URL = f"https://www.indeed.com/jobs?q={SEARCH_QUERY}&l={SEARCH_LOCATION}&start="
MAX_NEW = 500
RESULTS_PER_PAGE = 10
SCRAPED_FILE = "scraped_jobs.txt"
OUTPUT_CSV = "jobs.csv"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.3; rv:112.0) Gecko/20100101 Firefox/112.0"
]

PROXIES = [

    "http://mveselinovic858:KHuSyWq2gx@161.77.143.186:50100",


]

# ─── HELPERS ────────────────────────────────────────────────────────────────────


def get_random_proxy():
    return random.choice(PROXIES)


def init_driver(use_proxy=False):
    opts = uc.ChromeOptions()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")

    if use_proxy:
        proxy = get_random_proxy()
        opts.add_argument(f"--proxy-server={proxy}")
        print(f"\U0001F6E1️ Using proxy: {proxy}")

    driver = uc.Chrome(options=opts)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


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

    while new_count < MAX_NEW:
        start = page * RESULTS_PER_PAGE
        driver = init_driver(use_proxy=True)
        driver.get(f"{URL}{start}")

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.tapItem"))
            )
        except:
            print("No job cards found; stopping.")
            driver.quit()
            break

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))

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

            time.sleep(random.uniform(1, 2))

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

            time.sleep(random.uniform(1, 2))
            driver.back()
            time.sleep(random.uniform(1, 2))

        driver.quit()
        page += 1
        time.sleep(random.uniform(2, 4))

    print(f"Done: scraped {new_count} new remote jobs.")


if __name__ == "__main__":
    main()

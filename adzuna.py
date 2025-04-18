import requests
from bs4 import BeautifulSoup
import time
import csv
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
APP_ID = "fefbc0dc"
APP_KEY = "11faf14e2a6aa35e64fd4de5d22b3cfc"
API_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"
PAGE_SIZE = 5
MAX_NEW = 10
SCRAPED_FILE = "scraped_jobs.txt"
OUTPUT_CSV = "jobs.csv"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36"
)

BASE_PARAMS = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "results_per_page": PAGE_SIZE,
    "what": "software developer",
    "remote_only": 1,
    "salary_min": 50000,
    "content-type": "application/json"
}

# ─── SETUP ─────────────────────────────────────────────────────────────────────
if os.path.exists(SCRAPED_FILE):
    with open(SCRAPED_FILE) as f:
        scraped_urls = set(line.strip() for line in f if line.strip())
else:
    scraped_urls = set()

csv_is_new = not os.path.exists(OUTPUT_CSV)
csv_file = open(OUTPUT_CSV, "a", newline="", encoding="utf-8")
writer = csv.writer(csv_file)
if csv_is_new:
    writer.writerow(["title", "url", "description", "company"])

new_count = 0
page = 0

# ─── MAIN LOOP ─────────────────────────────────────────────────────────────────
while new_count < MAX_NEW:
    page += 1
    print(f"\nFetching API page {page}…")
    resp = requests.get(
        API_URL_TEMPLATE.format(page=page),
        params=BASE_PARAMS,
        headers={"User-Agent": USER_AGENT},
        timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        print("No more results from API; stopping.")
        break

    current_count = 0
    for job in results:
        current_count += 1
        if new_count >= MAX_NEW:
            break

        job_url = job.get("redirect_url")
        if not job_url or job_url in scraped_urls:
            print(f" {current_count} ▶ already scraped {job_url}")
            continue

        title = job.get("title", "").strip()
        # extract company name
        company = job.get("company", {}).get("display_name", "").strip()
        api_preview = job.get("description", "")
        # first 10 words from API description
        first10 = " ".join(api_preview.split()[:10])

        # Fetch the job detail page
        try:
            jd_resp = requests.get(
                job_url, headers={"User-Agent": USER_AGENT}, timeout=10
            )
            jd_resp.raise_for_status()
        except Exception as e:
            print(f"{current_count} ▶ failed to fetch detail for {job_url}: {e}")
            continue

        page_soup = BeautifulSoup(jd_resp.text, "html.parser")
        description = None

        # Find the <section> whose text contains those first10 words
        for section in page_soup.find_all("section"):
            text = section.get_text(" ", strip=True)
            if first10 in text:
                # replace <br> with newline, then strip all tags
                for br in section.find_all("br"):
                    br.replace_with("\n")
                description = section.get_text("\n", strip=True)
                break

        if not description:
            # fallback: entire page <p> tags
            ps = page_soup.find_all("p")
            description = "\n".join(p.get_text(strip=True) for p in ps)

        writer.writerow([title, job_url, description, company])
        csv_file.flush()

        with open(SCRAPED_FILE, "a") as sf:
            sf.write(job_url + "\n")

        scraped_urls.add(job_url)
        new_count += 1
        print(
            f"{current_count} => [{new_count}/{MAX_NEW}] {title} @ {company}")

        time.sleep(1)

    time.sleep(2)

csv_file.close()
print(f"\nDone. Scraped {new_count} new remote software‑developer jobs.")

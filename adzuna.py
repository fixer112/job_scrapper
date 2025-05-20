import requests
from bs4 import BeautifulSoup
import time
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ────────────────────────────────────────────────────────────────────
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

API_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"
PAGE_SIZE = 10
MAX_NEW = 10
JSON_FILE = "jobs.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36"
)

ONLY_EASY_APPLY = False

BASE_PARAMS = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "results_per_page": PAGE_SIZE,
    "what": "backend developer",  # php, laravel , web developer",'backend developer',
    # "where": "remote",
    "remote_only": 1,
    "salary_min": 50000,
    "content-type": "application/json",
    "max_days_old": 30,
    "sort_by": "date"
}

# ─── LOAD EXISTING JOBS ────────────────────────────────────────────────────────
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        all_jobs = json.load(f)
else:
    all_jobs = {}

print(f"Loaded {len(all_jobs)} existing jobs from {JSON_FILE}")

# ─── INITIAL
existing_urls = {job["url"] for job in all_jobs.values()}
# check existing titles - company names are not unique

existing_titles = {job["title"] + job["company"] for job in all_jobs.values()}
# total_existing_url_title = int((len(existing_urls) + len(existing_titles)) / 2)
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
    count = resp.json().get("count", 0)
    print(f"▶ Found {count} jobs")
    # count = count - total_existing_url_title

    # print(f"▶ {count} new jobs to process (excluding existing URLs and titles)")

    # if count <= 0:
    #     print("No new jobs to process; stopping.")
    #     break

    results = resp.json().get("results", [])
    if not results:
        print("No more results from API; stopping.")
        break

    for job in results:
        easy_apply = False
        if new_count >= MAX_NEW:
            break

        job_url = job.get("redirect_url")

        if "/details/" not in job_url:
            print(f"▶ Skipping non-detail URL: {job_url}")
            continue

        if not job_url or job_url in existing_urls:
            print(f"▶ Skipping already processed job: {job_url}")
            continue

        title = job.get("title", "").strip()
        company = job.get("company", {}).get("display_name", "").strip()
        n = f"{title}{company}"

        if n in existing_titles:
            print(
                f"▶ Skipping already processed title: {job['title']} {job['company']}")
            continue

        api_preview = job.get("description", "")
        first10 = " ".join(api_preview.split()[:10])

        try:
            jd_resp = requests.get(
                job_url, headers={"User-Agent": USER_AGENT}, timeout=10
            )
            jd_resp.raise_for_status()
        except Exception as e:
            print(f"▶ Failed to fetch detail for {job_url}: {e}")
            continue

        page_soup = BeautifulSoup(jd_resp.text, "html.parser")
        description = None

        for section in page_soup.find_all("section"):
            text = section.get_text(" ", strip=True)
            if "easy apply" in text.lower():
                easy_apply = True
            else:
                if ONLY_EASY_APPLY:
                    print(
                        f"▶ Skipping section without 'easy apply': {text[:50]}…")
                    continue

            if first10 in text:
                for br in section.find_all("br"):
                    br.replace_with("\n")
                description = section.get_text("\n", strip=True)
                break

            if "Sorry, this job is not available in your region" in text:
                print(
                    f"▶ Skipping job not available in your region: {job_url}")
                break

        if not description:
            ps = page_soup.find_all("p")
            description = "\n".join(p.get_text(strip=True) for p in ps)

        job_id = str(uuid.uuid4())
        added_title = "(EASY APPLY)" if easy_apply else ""
        all_jobs[job_id] = {
            "title": f"{title} {added_title}",
            "company": company,
            "description": description,
            "url": job_url,
            'file_url': None,
        }

        existing_urls.add(job_url)
        existing_titles.add(title)

        new_count += 1

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, indent=2, ensure_ascii=False)

        print(
            f"▶ Added [{new_count}/{MAX_NEW} of {count}] {title} @ {company}")

        time.sleep(1)

    time.sleep(2)


print(f"\n✅ Done. Scraped {new_count} new remote {BASE_PARAMS['what']} jobs.")

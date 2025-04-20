import json
import csv

# Load JSON
with open("jobs.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

# Define CSV file and fieldnames
with open("jobs.csv", "w", newline="", encoding="utf-8") as csv_file:
    fieldnames = ["title", "company", "description", "url", "file_url"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for uid, job in data.items():
        # Skip jobs without a title or company
        if not job.get("url") or not job.get("file_url"):
            print(f"Skipping job {uid} due to missing URL or file URL.")
            continue
        writer.writerow({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "description": job.get("description", "").strip().replace("\n", "")[:100],
            "url": job.get("url", ""),
            "file_url": job.get("file_url", "")
        })

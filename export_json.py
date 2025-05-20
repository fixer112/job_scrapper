import json
import csv


start_id = "e2af7b19-0433-430c-962e-ad3434647dc0"
end_id = None

id_started = False

# Load JSON
with open("jobs.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

# Define CSV file and fieldnames
with open("jobs.csv", "w", newline="", encoding="utf-8") as csv_file:
    fieldnames = ["title", "company", "url", "file_url"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()
    for uid, job in data.items():
        if start_id and uid != start_id and not id_started:
            # print(f"Skipping job {uid} until start_id {start_id} is found.")
            continue
        else:
            if not id_started:
                print(f"Found start_id {start_id}, starting to process jobs.")
                id_started = True

        if end_id and uid == end_id:
            print(f"Found end_id {end_id}, stopping processing.")
            break

        # Skip jobs without a title or company
        if not job.get("url") or not job.get("file_url"):
            print(f"Skipping job {uid} due to missing URL or file URL.")
            continue
        print(
            f"Processing job {uid} - {job.get('title', '')} at {job.get('company', '')}...")
        writer.writerow({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            # "description": job.get("description", "").strip().replace("\n", "")[:100],
            "url": job.get("url", ""),
            "file_url": job.get("file_url", "")
        })

import sys

if len(sys.argv) > 1:
    company = sys.argv[1]
else:
    company = "default"

print(f"\nFirma: {company}")

import os
import glob
import pandas as pd
from datetime import datetime

# ========================================
# PFAD SETUP (PRO FIRMA)
# ========================================

base_data_path = f"data/{company}"

raw_path = os.path.join(base_data_path, "raw")
processed_path = os.path.join(base_data_path, "processed")
exports_path = os.path.join(base_data_path, "exports")

os.makedirs(raw_path, exist_ok=True)
os.makedirs(processed_path, exist_ok=True)
os.makedirs(exports_path, exist_ok=True)

# ========================================
# HELPER
# ========================================

def find_latest_structured_job_file():

    preferred_files = [
        "job_details.csv",
        "jobs_latest.csv"
    ]

    for filename in preferred_files:

        path = os.path.join(
            processed_path,
            filename
        )

        if os.path.exists(path):
            return path

    return None


def normalize_job_frame(df):

    required_columns = {
        "title",
        "location",
        "company",
        "department"
    }

    if required_columns.issubset(df.columns):
        return df

    if "job_data" not in df.columns:
        raise ValueError("Unsupported CSV format.")

    normalized_rows = []

    for raw_value in df["job_data"].dropna():

        lines = [
            line.strip()
            for line in str(raw_value).splitlines()
            if line.strip()
        ]

        if len(lines) >= 4:

            title, location, company, department = lines[:4]

            normalized_rows.append({
                "title": title,
                "location": location,
                "company": company,
                "department": department
            })

    return pd.DataFrame(normalized_rows)


# ========================================
# DATEIEN (DYNAMISCH)
# ========================================

history_file = os.path.join(
    processed_path,
    "job_history.csv"
)

change_log_file = os.path.join(
    processed_path,
    "job_changes.csv"
)

department_file = os.path.join(
    processed_path,
    "department_summary.csv"
)

location_file = os.path.join(
    processed_path,
    "location_summary.csv"
)

# ========================================
# TIMESTAMPS
# ========================================

today = datetime.now().strftime("%Y-%m-%d")

current_timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

# ========================================
# DATEI FINDEN
# ========================================

latest_file = find_latest_structured_job_file()

if latest_file is None:

    files = glob.glob(
        os.path.join(raw_path, "*.csv")
    )

    latest_file = (
        max(files, key=os.path.getctime)
        if files else None
    )

if latest_file is None:
    raise FileNotFoundError("No CSV files found.")

print("\n========================================")
print("ANALYSIS PIPELINE STARTET")
print("========================================")

print("\nVerwendete Datei:")
print(latest_file)

# ========================================
# CSV LADEN
# ========================================

raw_df = pd.read_csv(latest_file)
df = normalize_job_frame(raw_df)

print("\nCSV erfolgreich geladen.")
print(f"\nJobs insgesamt:")
print(len(df))

# ========================================
# ANALYSEN
# ========================================

print("\n========================================")
print("DEPARTMENT ANALYSE")
print("========================================")

department_summary = (
    df["department"]
    .value_counts()
    .reset_index()
)

department_summary.columns = [
    "department",
    "count"
]

department_total = pd.DataFrame({
    "department": ["TOTAL"],
    "count": [department_summary["count"].sum()]
})

department_summary = pd.concat(
    [department_summary, department_total],
    ignore_index=True
)

print("\nJobs pro Department:\n")
print(department_summary)

print("\n========================================")
print("LOCATION ANALYSE")
print("========================================")

location_summary = (
    df["location"]
    .value_counts()
    .reset_index()
)

location_summary.columns = [
    "location",
    "count"
]

location_total = pd.DataFrame({
    "location": ["TOTAL"],
    "count": [location_summary["count"].sum()]
})

location_summary = pd.concat(
    [location_summary, location_total],
    ignore_index=True
)

print("\nJobs pro Standort:\n")
print(location_summary)

# ========================================
# SPEICHERN
# ========================================

department_summary.to_csv(department_file, index=False)
location_summary.to_csv(location_file, index=False)

print("\nZusammenfassungen gespeichert.")

# ========================================
# HISTORY
# ========================================

new_jobs = []
removed_jobs = []
reactivated_jobs = []

if not os.path.exists(history_file):

    history_df = df.copy()

    history_df["first_seen"] = today
    history_df["last_seen"] = today
    history_df["active"] = True

    history_df.to_csv(
        history_file,
        index=False
    )

    print("\nHistorie neu erstellt.")

    for _, row in df.iterrows():

        new_jobs.append({
            "title": row["title"],
            "location": row["location"]
        })

else:

    history_df = pd.read_csv(history_file)

    print("\nBestehende Historie geladen.")

    if "link" not in history_df.columns:

        print(
            "\n[WARN] Alte Historie ohne Link-Spalte erkannt."
        )

        history_df["link"] = ""

    for _, job in df.iterrows():

        mask = (
            history_df["link"] == job["link"]
        )

        if mask.any():

            was_active = history_df.loc[
                mask,
                "active"
            ].iloc[0]

            if not was_active:

                reactivated_jobs.append({
                    "title": job["title"],
                    "location": job["location"]
                })

            history_df.loc[
                mask,
                "last_seen"
            ] = today

            history_df.loc[
                mask,
                "active"
            ] = True

        else:

            new_row = {
                "title": job["title"],
                "location": job["location"],
                "company": job["company"],
                "department": job["department"],
                "link": job["link"],
                "mission": job.get(
                    "mission",
                    ""
                ),
                "requirements": job.get(
                    "requirements",
                    ""
                ),
                "benefits": job.get(
                    "benefits",
                    ""
                ),
                "scrape_timestamp": job.get(
                    "scrape_timestamp",
                    current_timestamp
                ),
                "first_seen": today,
                "last_seen": today,
                "active": True
            }

            history_df = pd.concat(
                [
                    history_df,
                    pd.DataFrame([new_row])
                ],
                ignore_index=True
            )

            new_jobs.append({
                "title": job["title"],
                "location": job["location"]
            })

    current_jobs = set(df["link"])

    for idx, row in history_df.iterrows():

        if pd.isna(row.get("link")):
            continue

        key = row["link"]

        if key not in current_jobs:

            if history_df.loc[
                idx,
                "active"
            ]:

                removed_jobs.append({
                    "title": row["title"],
                    "location": row["location"]
                })

            history_df.loc[
                idx,
                "active"
            ] = False

    history_df.to_csv(
        history_file,
        index=False
    )

    print("\nHistorie aktualisiert.")

    
# ========================================
# CHANGE LOG
# ========================================

change_rows = []

for job in new_jobs:
    change_rows.append({
        "date": today,
        "change_type": "NEW",
        "title": job["title"],
        "location": job["location"],
        "timestamp": current_timestamp
    })

for job in removed_jobs:
    change_rows.append({
        "date": today,
        "change_type": "REMOVED",
        "title": job["title"],
        "location": job["location"],
        "timestamp": current_timestamp
    })

for job in reactivated_jobs:
    change_rows.append({
        "date": today,
        "change_type": "REACTIVATED",
        "title": job["title"],
        "location": job["location"],
        "timestamp": current_timestamp
    })

if not change_rows:
    change_rows.append({
        "date": today,
        "change_type": "NO_CHANGES",
        "title": "-",
        "location": "-",
        "timestamp": current_timestamp
    })

changes_df = pd.DataFrame(change_rows)

if os.path.exists(change_log_file):

    try:
        old_changes_df = pd.read_csv(change_log_file)

        changes_df = pd.concat(
            [old_changes_df, changes_df],
            ignore_index=True
        )

    except Exception as e:
        print(
            "Fehler beim Laden der bestehenden Change-Historie:",
            e
        )

changes_df.to_csv(
    change_log_file,
    index=False
)

print("\nJob Change Log gespeichert:")
print(change_log_file)


# ========================================
# FINALE ÜBERSICHT
# ========================================

print("\n========================================")
print("FINALE ÜBERSICHT")
print("========================================")

print("\nHistorische Gesamtjobs:")
print(len(history_df))

print("\nAktive Jobs:")
print(history_df["active"].sum())

inactive_df = history_df[history_df["active"] == False]

print("\nInaktive Jobs:")
print(len(inactive_df))

if not inactive_df.empty:

    print("\nINAKTIVE JOBS:\n")

    for _, row in inactive_df.iterrows():
        print(f"- {row['title']} ({row['location']})")

print("\n========================================")
print("ANALYSIS PIPELINE ABGESCHLOSSEN")
print("========================================")
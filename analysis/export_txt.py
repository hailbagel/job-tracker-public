import sys

if len(sys.argv) > 1:
    company = sys.argv[1]
else:
    company = "default"

print(f"\nFirma: {company}")

import os
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
# DATEIEN
# ========================================

input_file = os.path.join(
    processed_path,
    "job_details.csv"
)

# ✅ TIMESTAMP IM DATEINAMEN (dein Wunsch)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

output_file = os.path.join(
    exports_path,
    f"{company}_job_details_{timestamp}.txt"
)

# ========================================
# START
# ========================================

print("\n========================================")
print("TXT EXPORT STARTET")
print("========================================")

# ========================================
# CSV LADEN
# ========================================

if not os.path.exists(input_file):
    print("\nERROR: Keine job_details.csv gefunden!")
    print(input_file)
    sys.exit(1)

df = pd.read_csv(input_file)

print("\nGeladene Jobs:")
print(len(df))

# ========================================
# TXT EXPORT
# ========================================

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    for idx, row in df.iterrows():

        title = row.get("title", "")
        location = row.get("location", "")
        company_name = row.get("company", "")
        department = row.get("department", "")
        mission = row.get("mission", "")
        requirements = row.get("requirements", "")
        benefits = row.get("benefits", "")

        f.write("\n")
        f.write("=" * 80)
        f.write("\n")

        f.write(f"JOB #{idx + 1}\n")

        f.write("=" * 80)
        f.write("\n\n")

        f.write(f"TITLE:\n{title}\n\n")
        f.write(f"LOCATION:\n{location}\n\n")
        f.write(f"COMPANY:\n{company_name}\n\n")
        f.write(f"DEPARTMENT:\n{department}\n\n")
        f.write(f"MISSION:\n{mission}\n\n")
        f.write(f"REQUIREMENTS:\n{requirements}\n\n")
        f.write(f"BENEFITS:\n{benefits}\n\n")

print("\nTXT Export gespeichert:")
print(output_file)

print("\n========================================")
print("TXT EXPORT ABGESCHLOSSEN")
print("========================================")
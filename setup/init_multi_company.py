import os
import json

# ========================================
# CONFIG
# ========================================

companies = [
    {
        "name": "neura",
        "enabled": False
    },
    {
        "name": "spacex",
        "enabled": True
    }
]

base_data_path = "data"
config_path = "configs"


# ========================================
# START
# ========================================

print("\n========================================")
print("INITIALISIERE MULTI-COMPANY SETUP")
print("========================================")

# ========================================
# CONFIGS ORDNER
# ========================================

os.makedirs(config_path, exist_ok=True)

companies_file = os.path.join(
    config_path,
    "companies.json"
)

with open(companies_file, "w") as f:
    json.dump(
        companies,
        f,
        indent=4
    )

print("\n✅ companies.json erstellt:")
print(companies_file)


# ========================================
# DATENSTRUKTUR ERSTELLEN
# ========================================

for company in companies:

    company_name = company["name"]

    print("\n----------------------------------------")
    print(f"Erstelle Struktur für: {company_name}")
    print("----------------------------------------")

    company_base = os.path.join(
        base_data_path,
        company_name
    )

    raw_path = os.path.join(
        company_base,
        "raw"
    )

    processed_path = os.path.join(
        company_base,
        "processed"
    )

    exports_path = os.path.join(
        company_base,
        "exports"
    )

    os.makedirs(raw_path, exist_ok=True)
    os.makedirs(processed_path, exist_ok=True)
    os.makedirs(exports_path, exist_ok=True)

    print("✅ erstellt:")
    print(f"  {raw_path}")
    print(f"  {processed_path}")
    print(f"  {exports_path}")


# ========================================
# ABSCHLUSS
# ========================================

print("\n========================================")
print("SETUP ABGESCHLOSSEN")
print("========================================")
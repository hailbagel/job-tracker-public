import pandas as pd
import html
import re
import os

# ----------------------------------------
# Dateien
# ----------------------------------------

input_file = "data/processed/job_details.csv"

output_file = "data/processed/job_details_cleaned.csv"

# ----------------------------------------
# CSV laden
# ----------------------------------------

print("\nLade Detaildaten...")

df = pd.read_csv(input_file)

print(f"Geladene Jobs: {len(df)}")

# ----------------------------------------
# Text Cleaning Funktion
# ----------------------------------------

def clean_text(text):

    # Falls leer
    if pd.isna(text):
        return ""

    # In String umwandeln
    text = str(text)

    # HTML Entities umwandeln
    # Beispiel:
    # &amp; -> &
    text = html.unescape(text)

    # Mehrfache Leerzeichen entfernen
    text = re.sub(r"\s+", " ", text)

    # Mehrfache Zeilenumbrüche entfernen
    text = re.sub(r"\n+", "\n", text)

    # Führende/trailing Spaces entfernen
    text = text.strip()

    return text

# ----------------------------------------
# Relevante Felder bereinigen
# ----------------------------------------

text_columns = [
    "title",
    "department",
    "mission",
    "requirements",
    "benefits"
]

for column in text_columns:

    print(f"\nBereinige Spalte: {column}")

    df[column] = df[column].apply(clean_text)

# ----------------------------------------
# Duplikate entfernen
# ----------------------------------------

before_count = len(df)

df = df.drop_duplicates(
    subset=["link"]
)

after_count = len(df)

removed = before_count - after_count

print(f"\nEntfernte Duplikate: {removed}")

# ----------------------------------------
# Optionale Qualitätsprüfung
# ----------------------------------------

print("\nPrüfe auf leere Felder...")

empty_missions = df["mission"].eq("").sum()

print(f"Leere Missionen: {empty_missions}")

empty_requirements = df["requirements"].eq("").sum()

print(f"Leere Requirements: {empty_requirements}")

# ----------------------------------------
# Speichern
# ----------------------------------------

os.makedirs(
    "data/processed",
    exist_ok=True
)

df.to_csv(
    output_file,
    index=False
)

# ----------------------------------------
# Zusammenfassung
# ----------------------------------------

print("\n========================================")
print("DATA CLEANING ABGESCHLOSSEN")
print("========================================")

print(f"\nSaubere Datei gespeichert unter:")
print(output_file)

print(f"\nFinale Datensätze:")
print(len(df))
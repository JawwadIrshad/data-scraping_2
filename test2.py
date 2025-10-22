import csv
from collections import Counter
import re

input_file = "filtered_businesses2.csv"
output_file = "output_no_duplicate_emails.csv"

# --- Read all rows ---
with open(input_file, "r", newline="", encoding="utf-8") as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)
    header = reader.fieldnames

# --- Detect email column ---
email_col = None
for col in header:
    if "email" in col.lower():
        email_col = col
        break

if not email_col:
    raise ValueError("❌ No email column found in CSV!")

# --- Helper to extract all emails from a row ---
def extract_emails(cell):
    if not cell:
        return []
    # Split on commas, semicolons, or spaces, remove junk
    parts = re.split(r'[;, ]+', cell)
    return [p.strip().lower() for p in parts if "@" in p]

# --- Count each individual email across the file ---
email_counts = Counter()
for row in rows:
    for email in extract_emails(row.get(email_col, "")):
        email_counts[email] += 1

# --- Keep only rows where *all* emails are unique (no duplicates anywhere) ---
filtered_rows = []
for row in rows:
    emails = extract_emails(row.get(email_col, ""))
    if all(email_counts[e] == 1 for e in emails):
        filtered_rows.append(row)

removed_count = len(rows) - len(filtered_rows)

# --- Write filtered data ---
with open(output_file, "w", newline="", encoding="utf-8") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=header)
    writer.writeheader()
    writer.writerows(filtered_rows)

print(f"✅ Removed {removed_count} rows with duplicate emails (across multiple emails per row).")
print(f"📂 Clean file saved as '{output_file}' with {len(filtered_rows)} unique rows.")

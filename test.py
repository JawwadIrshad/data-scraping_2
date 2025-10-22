import csv
import re

INPUT_CSV = "final2.csv"
OUTPUT_CSV = "filtered_businesses3.csv"
MAX_LENGTH = 40


# specific bad phrases you want to replace directly
BAD_BUSINESS_PHRASES = [
    "compass",
    "undefined",
    "experience"
]


def contains_bad_phrase(name):
    """Check if business name contains any unwanted phrases."""
    name_lower = name.lower()
    for phrase in BAD_BUSINESS_PHRASES:
        if phrase.lower() in name_lower:
            return True
    return False


def fix_incomplete_sentence(name):
    """Trim name cleanly at MAX_LENGTH without breaking words."""
    name = name.strip()
    if len(name) <= MAX_LENGTH:
        return name

    trimmed = name[:MAX_LENGTH]
    if " " in trimmed:
        trimmed = trimmed[:trimmed.rfind(" ")]
    return trimmed.strip()


def process_csv():
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        name_col = None
        agent_col = None

        # detect business and agent columns automatically
        for col in fieldnames:
            if "business" in col.lower() or "company" in col.lower():
                name_col = col
            if "agent" in col.lower() or "name" in col.lower() or "contact" in col.lower():
                agent_col = col

        if not name_col:
            print("❌ No 'Business Name' column found.")
            return

        if not agent_col:
            print("⚠️ No 'Agent Name' column found — will skip replacements.")

        new_rows = []
        replaced_count = 0

        for row in reader:
            business_name = (row.get(name_col) or "").strip()
            agent_name = (row.get(agent_col) or "").strip()

            # replace if matches bad phrases
            if not business_name or contains_bad_phrase(business_name):
                if agent_name:
                    row[name_col] = f"{agent_name} Realtors"
                    replaced_count += 1
                else:
                    row[name_col] = ""
            else:
                row[name_col] = fix_incomplete_sentence(business_name)

            new_rows.append(row)

        print(f"✅ Processed {len(new_rows)} rows.")
        print(f"🔁 Replaced {replaced_count} business names with agent name + Realtors.")

    # save updated data
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)

    print(f"🎯 Saved clean names to '{OUTPUT_CSV}'")


if __name__ == "__main__":
    process_csv()

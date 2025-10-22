import pandas as pd
import csv

# --- FILE PATHS ---
main_csv = "filtered_businesses.csv"   # main dataset
email_list_csv = "deliverable_rows.csv"  # list of deliverable emails
output_csv = "matched_results2.csv"       # output file

# --- READ FILES ---
df_main = pd.read_csv(main_csv, dtype=str, quoting=csv.QUOTE_ALL)
df_emails = pd.read_csv(email_list_csv, dtype=str)

# --- DETECT EMAIL COLUMNS ---
email_col_main = [col for col in df_main.columns if "email" in col.lower()][0]
email_col_list = [col for col in df_emails.columns if "email" in col.lower()][0]

# --- CLEAN EMAILS ---
emails_to_match = set(df_emails[email_col_list].dropna().str.strip().str.lower())

def extract_matched_email(email_field):
    """Return only the matching email (keep full row, remove other emails)."""
    if pd.isna(email_field):
        return None

    # Split emails by commas or semicolons
    emails = [e.strip().lower() for e in str(email_field).replace(';', ',').split(',') if e.strip()]
    
    # Find the first matched email
    for e in emails:
        if e in emails_to_match:
            return e  # keep only the matched one
    return None  # no match found

# --- APPLY MATCHING ---
df_main['matched_email'] = df_main[email_col_main].apply(extract_matched_email)

# Keep only rows where a match was found
matched_rows = df_main[df_main['matched_email'].notna()].copy()

# Replace the original email field with the single matched email
matched_rows[email_col_main] = matched_rows['matched_email']
matched_rows.drop(columns=['matched_email'], inplace=True)

# --- SAVE RESULT ---
matched_rows.to_csv(output_csv, index=False, quoting=csv.QUOTE_ALL)

print(f"✅ Matched rows saved to {output_csv}. Total matches: {len(matched_rows)}")

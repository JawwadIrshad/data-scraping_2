import re
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ============================================================
# ================ SCRIPT 1 — BUSINESS NAME FIX ===============
# ============================================================

# === CONFIG ===
SERVICE_ACCOUNT_FILE = 'service_account.json'  # your credentials file
SPREADSHEET_ID = '1zJaPugKdJXdDJa1ouhDdkzMtbQOk3n6PHpBdwF0Gma4'  # Google Sheet ID
SHEET_NAME = 'Sheet5'  # tab name

# === AUTH ===
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# === READ ALL DATA ===
data = sheet.get_all_records()
headers = sheet.row_values(1)

BUSINESS_COL_NAME = "Business Name"
AGENT_COL_NAME = "Agent Name"

# === Verify both columns exist ===
if BUSINESS_COL_NAME not in headers or AGENT_COL_NAME not in headers:
    raise Exception(f"Missing required columns: '{BUSINESS_COL_NAME}' or '{AGENT_COL_NAME}'")

business_col = headers.index(BUSINESS_COL_NAME) + 1
agent_col = headers.index(AGENT_COL_NAME) + 1

# === Function to detect bad business names ===
def is_invalid_business_name(name):
    if not name or str(name).strip() == "":
        return True
    name = str(name).lower().strip()
    return bool(re.search(r"\byears?\b", name)) or "experience" in name or "business" in name or "undefined" in name or "compass" in name

# === Collect updates ===
updates = []
for i, row in enumerate(data, start=2):
    business_val = str(row.get(BUSINESS_COL_NAME, "")).strip()
    agent_val = str(row.get(AGENT_COL_NAME, "")).strip()

    if agent_val and is_invalid_business_name(business_val):
        updates.append((i, agent_val))

# === Apply updates in batch ===
if updates:
    cell_updates = []
    for row_num, value in updates:
        cell_updates.append({
            'range': f'{chr(64 + business_col)}{row_num}',
            'values': [[value]]
        })
    sheet.batch_update([{'range': u['range'], 'values': u['values']} for u in cell_updates])
    print(f"✅ Script 1: Updated {len(updates)} rows.")
else:
    print("✅ Script 1: No invalid Business_Name cells found.")



# ============================================================
# ================ SCRIPT 2 — PHONE CLEANER ===================
# ============================================================

# === CONFIGURATION ===
SERVICE_ACCOUNT_FILE = 'service_account.json'
SPREADSHEET_ID = '1zJaPugKdJXdDJa1ouhDdkzMtbQOk3n6PHpBdwF0Gma4'
SHEET_NAME = 'Sheet5'

# === AUTHENTICATION ===
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client = gspread.authorize(credentials)

# === OPEN SHEET ===
sheet2 = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# === READ DATA ===
rows = sheet2.get_all_values()
if not rows:
    print("❌ Script 2: Sheet is empty.")
else:
    header = rows[0]
    data = rows[1:]

    def find_col(header, keyword):
        for i, col in enumerate(header):
            if keyword.lower() in col.lower():
                return i
        return None

    phone_col = find_col(header, 'phone')
    if phone_col is None:
        raise ValueError("❌ Script 2: Could not find a column containing 'phone'.")

    def clean_phone(phone):
        digits = re.sub(r'\D', '', str(phone))
        if not digits:
            return ''
        if digits.startswith('1') and len(digits) == 11:
            return f"+{digits}"
        elif len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) > 11 and digits.startswith('00'):
            return f"+{digits[2:]}"
        else:
            return f"+{digits}"

    updated_data = []
    seen_numbers = set()
    removed_invalid = 0
    removed_duplicates = 0

    for row in data:
        if len(row) <= phone_col:
            continue

        phone_raw = row[phone_col]
        cleaned = clean_phone(phone_raw)
        digits_only = re.sub(r'\D', '', cleaned)

        if len(digits_only) < 11:
            removed_invalid += 1
            continue

        if digits_only in seen_numbers:
            removed_duplicates += 1
            continue

        seen_numbers.add(digits_only)
        row[phone_col] = cleaned
        updated_data.append(row)

    # Rewrite sheet
    sheet2.clear()
    sheet2.append_row(header)
    if updated_data:
        sheet2.append_rows(updated_data)

    print("✅ Script 2 Complete:")
    print(f"📱 Valid unique rows: {len(updated_data)}")
    print(f"🧹 Removed invalid phones: {removed_invalid}")
    print(f"🚫 Removed duplicates: {removed_duplicates}")



# ============================================================
# ============ SCRIPT 3 — TRIMMER & BUSINESS FIX =============
# ============================================================

SERVICE_ACCOUNT_FILE = 'service_account.json'
SPREADSHEET_ID = '1zJaPugKdJXdDJa1ouhDdkzMtbQOk3n6PHpBdwF0Gma4'
SOURCE_SHEET = 'Sheet5'
DEST_SHEET = 'clean_data01'
MAX_LENGTH = 40

BAD_BUSINESS_PHRASES = ["Compass", "undefined", "experience"]

def contains_bad_phrase(name):
    name_lower = name.lower()
    return any(phrase.lower() in name_lower for phrase in BAD_BUSINESS_PHRASES)

def fix_incomplete_sentence(name):
    name = name.strip()
    if len(name) <= MAX_LENGTH:
        return name
    trimmed = name[:MAX_LENGTH]
    if " " in trimmed:
        trimmed = trimmed[:trimmed.rfind(" ")]
    return trimmed.strip()

def process_sheet():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet3 = client.open_by_key(SPREADSHEET_ID)

    worksheet = sheet3.worksheet(SOURCE_SHEET)
    data = worksheet.get_all_records()
    if not data:
        print("❌ Script 3: No data found.")
        return

    fieldnames = list(data[0].keys())
    name_col = None
    agent_col = None

    for col in fieldnames:
        if "business" in col.lower() or "company" in col.lower():
            name_col = col
        if "agent" in col.lower() or "name" in col.lower() or "contact" in col.lower():
            agent_col = col

    if not name_col:
        print("❌ Script 3: No business name column.")
        return

    new_rows = []
    replaced_count = 0

    for row in data:
        # business_name = (row.get(name_col) or "").strip()
        # agent_name = str(row.get(agent_col) or "").strip()
        business_name = str(row.get(name_col) or "").strip()
        agent_name = str(row.get(agent_col) or "").strip()


        if not business_name or contains_bad_phrase(business_name):
            if agent_name:
                row[name_col] = f"{agent_name} Realtors"
                replaced_count += 1
            else:
                row[name_col] = ""
        else:
            row[name_col] = fix_incomplete_sentence(business_name)

        new_rows.append([row.get(col, "") for col in fieldnames])

    print(f"✅ Script 3: Processed {len(new_rows)} rows.")
    print(f"🔁 Replaced: {replaced_count}")

    try:
        dest_ws = sheet3.worksheet(DEST_SHEET)
        dest_ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        dest_ws = sheet3.add_worksheet(title=DEST_SHEET, rows=len(new_rows)+10, cols=len(fieldnames))

    dest_ws.append_row(fieldnames)
    dest_ws.append_rows(new_rows)

process_sheet()



# ============================================================
# ============== SCRIPT 4 — REMOVE DUPLICATES =================
# ============================================================

SHEET_ID = "1zJaPugKdJXdDJa1ouhDdkzMtbQOk3n6PHpBdwF0Gma4"
TAB_NAME = "Sheet5"
DUP_TAB_NAME = "Duplicates2"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
client = gspread.authorize(creds)

sheet4 = client.open_by_key(SHEET_ID)
try:
    ws = sheet4.worksheet(TAB_NAME)
except gspread.exceptions.WorksheetNotFound:
    ws = sheet4.add_worksheet(title=TAB_NAME, rows=1000, cols=2)

data = ws.get_all_values()
if data:
    df = pd.DataFrame(data)

    def clean_text(text):
        if not isinstance(text, str):
            return ""
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        return text.lower()

    df['_clean'] = df[0].apply(clean_text)

    duplicates = df[df.duplicated(subset=['_clean'], keep="first")]
    unique_df = df.drop_duplicates(subset=['_clean'], keep="first").drop(columns=['_clean'])

    if not duplicates.empty:
        ws.clear()
        ws.update(unique_df.iloc[:, :-1].values.tolist())

        try:
            dup_ws = sheet4.worksheet(DUP_TAB_NAME)
            dup_ws.clear()
        except gspread.exceptions.WorksheetNotFound:
            dup_ws = sheet4.add_worksheet(title=DUP_TAB_NAME, rows=1000, cols=len(df.columns))

        dup_ws.update(duplicates.iloc[:, :-1].values.tolist())
        print(f"✅ Script 4: {len(duplicates)} duplicates moved.")
    else:
        print("✅ Script 4: No duplicates found.")
else:
    print("❌ Script 4: No data found.")

# ============================================================
# ====================== END OF MAIN.PY =======================
# ============================================================


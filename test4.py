import pandas as pd

# === File paths ===
input_file = "cleaned_output.csv"     # Replace with your input CSV file name
output_file = "output_with_plus3.csv"  # Output file name

# === Read CSV ===
df = pd.read_csv(input_file)

# === Automatically detect phone number column ===
phone_col = [col for col in df.columns if "phone" in col.lower()]
if not phone_col:
    raise ValueError("❌ No phone number column found.")
phone_col = phone_col[0]
print(f"📞 Detected phone column: {phone_col}")

# === Function to add '+' ===
def add_plus(num):
    if pd.isna(num):
        return num
    num_str = str(num).strip()
    if not num_str:
        return num_str
    # Add '+' if missing and number starts with a digit
    if not num_str.startswith('+') and num_str[0].isdigit():
        return '+' + num_str
    return num_str

# === Apply to the phone column ===
df[phone_col] = df[phone_col].apply(add_plus)

# === Save the updated file ===
df.to_csv(output_file, index=False)

print(f"✅ Updated phone numbers saved to '{output_file}'")

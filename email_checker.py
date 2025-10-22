import pandas as pd

# --- CONFIGURATION ---
input_file = "output_output4.csv"           # Replace with your actual file name
output_file = "undeliverable_rows.csv"  # Output file name

# --- READ THE CSV ---
df = pd.read_csv(input_file)

# --- CHECK IF 'Validation Status' COLUMN EXISTS ---
if "Validation Status" not in df.columns:
    raise ValueError("❌ The CSV file does not contain a 'Validation Status' column.")

# --- FILTER FOR DELIVERABLE ROWS ---
deliverable_df = df[df["Validation Status"].astype(str).str.lower() == "undeliverable"]

# --- SAVE TO NEW CSV ---
deliverable_df.to_csv(output_file, index=False)

print(f"✅ Successfully saved {len(deliverable_df)} Deliverable rows to '{output_file}'.")

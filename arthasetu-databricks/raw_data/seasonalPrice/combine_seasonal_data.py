import pandas as pd
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the files and their corresponding years
files_and_years = [
    ("Season_Price_Arrival_1.csv", "2021-22"),
    ("Season_Price_Arrival_2.csv", "2022-23"),
    ("Season_Price_Arrival_3.csv", "2023-24"),
    ("Season_Price_Arrival_4.csv", "2024-25"),
    ("Season_Price_Arrival_5.csv", "2025-26"),
]

# Standardized column names
standard_columns = [
    "Commodity_Group",
    "Commodity",
    "MSP_Rs_Per_Quintal",
    "Kharif_Season_Price_Rs_Per_Quintal",
    "Kharif_Season_Arrival_Metric_Tonnes",
    "Rabi_Season_Price_Rs_Per_Quintal",
    "Rabi_Season_Arrival_Metric_Tonnes",
]

all_dfs = []

for filename, year in files_and_years:
    filepath = os.path.join(base_dir, filename)
    
    # Read CSV, skip the first 2 header/title rows, use row 3 (index 2) as header
    df = pd.read_csv(filepath, skiprows=2, header=0, encoding="utf-8")
    
    # Drop any fully empty rows
    df = df.dropna(how="all")
    
    # Also drop rows where the first two columns are both NaN (trailing junk)
    df = df.dropna(subset=[df.columns[0], df.columns[1]], how="all")
    
    # Rename columns to standardized names
    df.columns = standard_columns
    
    # Replace '-' with NaN for cleanliness
    df = df.replace("-", pd.NA)
    
    # Add year and source file columns
    df.insert(0, "Year", year)
    df.insert(1, "Source_File", filename)
    
    # Convert numeric columns (they may have commas or be read as strings)
    numeric_cols = [
        "MSP_Rs_Per_Quintal",
        "Kharif_Season_Price_Rs_Per_Quintal",
        "Kharif_Season_Arrival_Metric_Tonnes",
        "Rabi_Season_Price_Rs_Per_Quintal",
        "Rabi_Season_Arrival_Metric_Tonnes",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    all_dfs.append(df)
    print(f"✓ Loaded {filename} ({year}): {len(df)} rows")

# Combine all dataframes
combined = pd.concat(all_dfs, ignore_index=True)

# Sort by Year, Commodity Group, Commodity for clean ordering
combined = combined.sort_values(
    by=["Year", "Commodity_Group", "Commodity"],
    ignore_index=True
)

# Save combined file
output_path = os.path.join(base_dir, "Season_Price_Arrival_Combined.csv")
combined.to_csv(output_path, index=False)

print(f"\n{'='*60}")
print(f"Combined file saved: {output_path}")
print(f"Total rows: {len(combined)}")
print(f"Years covered: {sorted(combined['Year'].unique())}")
print(f"Unique commodities: {combined['Commodity'].nunique()}")
print(f"Unique commodity groups: {combined['Commodity_Group'].nunique()}")
print(f"\nColumns in output:")
for col in combined.columns:
    print(f"  - {col}")
print(f"\nPreview (first 10 rows):")
print(combined.head(10).to_string(index=False))

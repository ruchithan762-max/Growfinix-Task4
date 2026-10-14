
import pandas as pd
import sqlite3
from pathlib import Path

# --------------------------------
# 1. Set up file locations
# --------------------------------

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "media_costs.csv"
SQL_FILE = BASE_DIR / "task4_queries.sql"
OUTPUT_DIR = BASE_DIR / "output"
DB_FILE = OUTPUT_DIR / "media_costs.db"

# --------------------------------
# 2. Check input files
# --------------------------------

if not CSV_FILE.exists():
    raise FileNotFoundError(
        f"CSV file not found: {CSV_FILE}\n"
        "Make sure media_costs.csv is in the same folder as this Python file."
    )

if not SQL_FILE.exists():
    raise FileNotFoundError(
        f"SQL file not found: {SQL_FILE}\n"
        "Make sure task4_queries.sql is in the same folder."
    )

# --------------------------------
# 3. Create output folder
# --------------------------------

if OUTPUT_DIR.exists() and not OUTPUT_DIR.is_dir():
    raise NotADirectoryError(
        f"{OUTPUT_DIR} is a file, not a folder. "
        "Rename that file and run the program again."
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------
# 4. Read and clean CSV data
# --------------------------------

print("Reading CSV file:", CSV_FILE)

df = pd.read_csv(CSV_FILE, encoding="utf-8-sig")

# Clean column names: remove spaces and normalize names
df.columns = [
    str(column).strip().replace(" ", "_").replace("-", "_")
    for column in df.columns
]

# Handle common alternative column names
column_mapping = {
    "AssetID": "Asset_ID",
    "asset_id": "Asset_ID",
    "MediaFormat": "Media_Format",
    "media_format": "Media_Format",
    "ProductionCost": "Production_Cost",
    "production_cost": "Production_Cost",
    "Cost": "Production_Cost",
    "Revenue": "Revenue",
    "revenue": "Revenue",
}

df = df.rename(columns=column_mapping)

required_columns = [
    "Asset_ID",
    "Media_Format",
    "Production_Cost",
    "Revenue",
]

print("CSV columns detected:", list(df.columns))

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}\n"
        f"Columns found: {list(df.columns)}\n"
        "Required columns: Asset_ID, Media_Format, "
        "Production_Cost, Revenue.\n"
        "Please check the first row of media_costs.csv."
    )

# Keep only required columns
df = df[required_columns].copy()

# Clean text fields
df["Asset_ID"] = df["Asset_ID"].astype(str).str.strip()
df["Media_Format"] = df["Media_Format"].astype(str).str.strip()

# Convert costs and revenue into numbers
df["Production_Cost"] = pd.to_numeric(
    df["Production_Cost"], errors="coerce"
)
df["Revenue"] = pd.to_numeric(
    df["Revenue"], errors="coerce"
)

# Remove rows with missing or invalid values
before_cleaning = len(df)
df = df.dropna(subset=required_columns)
df = df.drop_duplicates(subset=["Asset_ID"])

print("Rows before cleaning:", before_cleaning)
print("Rows after cleaning:", len(df))

if df.empty:
    raise ValueError(
        "No valid rows remain after cleaning. "
        "Check the values in media_costs.csv."
    )

# Calculate profit for each asset
df["Profit"] = df["Revenue"] - df["Production_Cost"]

# Calculate individual asset ROI
df["ROI_Percent"] = (
    df["Profit"] / df["Production_Cost"].replace(0, float("nan"))
) * 100

# Save cleaned data
cleaned_csv = OUTPUT_DIR / "media_costs_cleaned.csv"
df.to_csv(cleaned_csv, index=False)

# --------------------------------
# 5. Create SQLite database
# --------------------------------

connection = sqlite3.connect(DB_FILE)

try:
    df[required_columns].to_sql(
        "media_costs",
        connection,
        if_exists="replace",
        index=False
    )

    print("\nSQLite database created successfully.")

    # --------------------------------
    # 6. Run SQL queries
    # --------------------------------

    sql_text = SQL_FILE.read_text(encoding="utf-8-sig")
    queries = [
        query.strip()
        for query in sql_text.split(";")
        if query.strip()
    ]

    for number, query in enumerate(queries, start=1):
        try:
            result = pd.read_sql_query(query, connection)

            output_file = (
                OUTPUT_DIR / f"query_{number}_results.csv"
            )
            result.to_csv(output_file, index=False)

            print(f"\nQuery {number} result:")
            print(result.to_string(index=False))
            print("Saved:", output_file.name)

        except Exception as error:
            print(f"\nError in SQL query {number}: {error}")

    # --------------------------------
    # 7. Generate ROI summary
    # --------------------------------

    summary = df.groupby("Media_Format", as_index=False).agg(
        Total_Production_Cost=("Production_Cost", "sum"),
        Total_Revenue=("Revenue", "sum"),
        Total_Profit=("Profit", "sum"),
    )

    summary["ROI_Percent"] = (
        summary["Total_Profit"]
        / summary["Total_Production_Cost"].replace(0, float("nan"))
    ) * 100

    summary_file = OUTPUT_DIR / "media_format_roi_summary.csv"
    summary.to_csv(summary_file, index=False)

    print("\nFINAL MEDIA FORMAT ROI SUMMARY")
    print(summary.to_string(index=False))

    print("\nSUCCESS! Task 4 analysis completed.")
    print("Check the output folder:", OUTPUT_DIR)

finally:
    connection.close()

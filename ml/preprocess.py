from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "CICIDS2017"
    / "MachineLearningCSV"
    / "MachineLearningCVE"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cicids2017_cleaned.csv"


# --------------------------------------------------
# Find CSV files
# --------------------------------------------------

csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in: {DATA_DIR}"
    )

print(f"Found {len(csv_files)} CSV files.")


# --------------------------------------------------
# Start fresh output file
# --------------------------------------------------

if OUTPUT_FILE.exists():
    OUTPUT_FILE.unlink()

first_chunk = True

total_rows = 0
total_inf_values = 0


# --------------------------------------------------
# Process one CSV at a time
# --------------------------------------------------

for file in csv_files:

    print(f"\nProcessing: {file.name}")

    file_rows = 0
    file_inf_values = 0

    # Read the large CSV in chunks
    for chunk in pd.read_csv(
        file,
        skipinitialspace=True,
        low_memory=False,
        chunksize=100_000
    ):

        # Clean column names
        chunk.columns = chunk.columns.str.strip()

        # Check Label column
        if "Label" not in chunk.columns:
            raise ValueError(
                f"Label column not found in {file.name}"
            )

        # Clean labels
        chunk["Label"] = (
            chunk["Label"]
            .astype(str)
            .str.strip()
        )

        # Replace infinite numeric values with NaN
        numeric_columns = chunk.select_dtypes(
            include=[np.number]
        ).columns

        inf_count = np.isinf(
            chunk[numeric_columns].to_numpy()
        ).sum()

        file_inf_values += int(inf_count)

        chunk[numeric_columns] = (
            chunk[numeric_columns]
            .replace([np.inf, -np.inf], np.nan)
        )

        # Remove rows without a valid label
        before = len(chunk)

        chunk = chunk[
            chunk["Label"].notna()
            & (chunk["Label"] != "")
        ]

        file_rows += len(chunk)

        # Write chunk to output
        chunk.to_csv(
            OUTPUT_FILE,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

    total_rows += file_rows
    total_inf_values += file_inf_values

    print(f"Rows processed: {file_rows:,}")
    print(f"Infinite values replaced: {file_inf_values:,}")


# --------------------------------------------------
# Final summary
# --------------------------------------------------

print("\n========================================")
print("CLEANING COMPLETED SUCCESSFULLY")
print("========================================")

print(f"Total rows written: {total_rows:,}")
print(f"Total infinite values replaced: {total_inf_values:,}")
print(f"Output file: {OUTPUT_FILE}")
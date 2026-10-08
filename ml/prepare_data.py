import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CLEANED_FILE = BASE_DIR / "data" / "processed" / "cicids2017_cleaned.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

TRAIN_FILE = OUTPUT_DIR / "cicids2017_train.csv"
TEST_FILE = OUTPUT_DIR / "cicids2017_test.csv"
METADATA_FILE = OUTPUT_DIR / "cicids2017_metadata.json"

CHUNK_SIZE = 100_000
TEST_SIZE = 0.20
RANDOM_STATE = 42


# ============================================================
# CHECK INPUT FILE
# ============================================================

if not CLEANED_FILE.exists():
    raise FileNotFoundError(
        f"Cleaned dataset not found:\n{CLEANED_FILE}"
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("AEGIS ONE - DATA PREPARATION")
print("=" * 70)

print(f"\nInput file:")
print(CLEANED_FILE)


# ============================================================
# STEP 1: READ LABELS ONLY
# This avoids loading the entire dataset into memory.
# ============================================================

print("\n[1/5] Reading labels...")

label_chunks = []

for chunk in pd.read_csv(
    CLEANED_FILE,
    usecols=["Label"],
    chunksize=CHUNK_SIZE,
    low_memory=False
):
    labels = chunk["Label"].astype(str).str.strip()

    label_chunks.append(labels.to_numpy())

all_labels = np.concatenate(label_chunks)

print(f"Total rows: {len(all_labels):,}")


# ============================================================
# STEP 2: ENCODE LABELS
# ============================================================

print("\n[2/5] Encoding attack labels...")

label_encoder = LabelEncoder()

encoded_labels = label_encoder.fit_transform(all_labels)

classes = label_encoder.classes_

print(f"Number of classes: {len(classes)}")

print("\nLabel mapping:")

for index, label in enumerate(classes):
    print(f"{index:2d} -> {label}")


# ============================================================
# STEP 3: STRATIFIED TRAIN / TEST SPLIT
# ============================================================

print("\n[3/5] Creating stratified train/test split...")

row_indices = np.arange(len(all_labels))

train_indices, test_indices = train_test_split(
    row_indices,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=encoded_labels
)

train_mask = np.zeros(len(all_labels), dtype=bool)
train_mask[train_indices] = True

print(f"Training rows: {len(train_indices):,}")
print(f"Testing rows : {len(test_indices):,}")


# ============================================================
# STEP 4: FIND MEDIAN VALUES FROM TRAINING DATA ONLY
# ============================================================

print("\n[4/5] Calculating training-set median values...")

# These are the columns that contained missing values
# during the cleaning stage.

IMPUTE_COLUMNS = [
    "Flow Bytes/s",
    "Flow Packets/s"
]

median_values = {}

current_position = 0

median_data = {
    column: []
    for column in IMPUTE_COLUMNS
}

for chunk in pd.read_csv(
    CLEANED_FILE,
    chunksize=CHUNK_SIZE,
    low_memory=False
):

    chunk_length = len(chunk)

    start = current_position
    end = current_position + chunk_length

    local_train_mask = train_mask[start:end]

    if local_train_mask.any():

        train_chunk = chunk.loc[local_train_mask]

        for column in IMPUTE_COLUMNS:

            values = pd.to_numeric(
                train_chunk[column],
                errors="coerce"
            )

            valid_values = values.dropna().to_numpy()

            if len(valid_values) > 0:
                median_data[column].append(valid_values)

    current_position = end


for column in IMPUTE_COLUMNS:

    if median_data[column]:

        all_values = np.concatenate(median_data[column])

        median_values[column] = float(
            np.median(all_values)
        )

    else:
        median_values[column] = 0.0

    print(
        f"{column}: "
        f"{median_values[column]}"
    )


# ============================================================
# STEP 5: CREATE TRAINING AND TEST CSV FILES
# ============================================================

print("\n[5/5] Creating training and testing datasets...")

# Remove old files if they already exist
if TRAIN_FILE.exists():
    TRAIN_FILE.unlink()

if TEST_FILE.exists():
    TEST_FILE.unlink()


first_train_chunk = True
first_test_chunk = True

current_position = 0

total_train_written = 0
total_test_written = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(
        CLEANED_FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ),
    start=1
):

    chunk_length = len(chunk)

    start = current_position
    end = current_position + chunk_length

    local_train_mask = train_mask[start:end]

    local_test_mask = ~local_train_mask

    # --------------------------------------------------------
    # Clean feature columns
    # --------------------------------------------------------

    feature_columns = [
        column
        for column in chunk.columns
        if column != "Label"
    ]

    for column in feature_columns:

        chunk[column] = pd.to_numeric(
            chunk[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Fill missing values using TRAINING medians
    # --------------------------------------------------------

    for column, median_value in median_values.items():

        if column in chunk.columns:
            chunk[column] = chunk[column].fillna(
                median_value
            )

    # --------------------------------------------------------
    # Encode labels
    # --------------------------------------------------------

    chunk["Label"] = label_encoder.transform(
        chunk["Label"].astype(str).str.strip()
    )

    # --------------------------------------------------------
    # Split current chunk
    # --------------------------------------------------------

    train_chunk = chunk.loc[local_train_mask]
    test_chunk = chunk.loc[local_test_mask]

    # --------------------------------------------------------
    # Write training data
    # --------------------------------------------------------

    train_chunk.to_csv(
        TRAIN_FILE,
        mode="w" if first_train_chunk else "a",
        header=first_train_chunk,
        index=False
    )

    # --------------------------------------------------------
    # Write testing data
    # --------------------------------------------------------

    test_chunk.to_csv(
        TEST_FILE,
        mode="w" if first_test_chunk else "a",
        header=first_test_chunk,
        index=False
    )

    first_train_chunk = False
    first_test_chunk = False

    total_train_written += len(train_chunk)
    total_test_written += len(test_chunk)

    current_position = end

    print(
        f"Processed chunk {chunk_number} | "
        f"Rows processed: {current_position:,}"
    )


# ============================================================
# SAVE METADATA
# ============================================================

metadata = {
    "dataset": "CICIDS2017",
    "source_file": str(CLEANED_FILE),
    "total_rows": int(len(all_labels)),
    "training_rows": int(total_train_written),
    "testing_rows": int(total_test_written),
    "test_size": TEST_SIZE,
    "random_state": RANDOM_STATE,
    "classes": classes.tolist(),
    "imputation": median_values,
    "label_encoding": {
        str(index): label
        for index, label in enumerate(classes)
    }
}


with open(
    METADATA_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DATA PREPARATION COMPLETE")
print("=" * 70)

print(f"\nTraining rows : {total_train_written:,}")
print(f"Testing rows  : {total_test_written:,}")

print(f"\nTraining file:")
print(TRAIN_FILE)

print(f"\nTesting file:")
print(TEST_FILE)

print(f"\nMetadata file:")
print(METADATA_FILE)

print("\nLabel encoding:")
for index, label in enumerate(classes):
    print(f"{index:2d} -> {label}")

print("\nAegis One dataset is now ready for ML training.")
import gc
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = BASE_DIR / "data" / "processed" / "cicids2017_train.csv"
TEST_FILE = BASE_DIR / "data" / "processed" / "cicids2017_test.csv"
METADATA_FILE = BASE_DIR / "data" / "processed" / "cicids2017_metadata.json"

MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_FILE = MODEL_DIR / "aegis_xgboost.json"
METRICS_FILE = MODEL_DIR / "xgboost_metrics.json"

CACHE_DIR = MODEL_DIR / "xgboost_cache"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

CHUNK_SIZE = 100_000

N_ESTIMATORS = 150
MAX_DEPTH = 8
LEARNING_RATE = 0.1

SUBSAMPLE = 0.8
COLSAMPLE_BYTREE = 0.8

RANDOM_STATE = 42


print("=" * 70)
print("AEGIS ONE - MEMORY-EFFICIENT XGBOOST TRAINING")
print("=" * 70)


# ============================================================
# CHECK FILES
# ============================================================

if not TRAIN_FILE.exists():
    raise FileNotFoundError(
        f"Training file not found:\n{TRAIN_FILE}"
    )

if not TEST_FILE.exists():
    raise FileNotFoundError(
        f"Testing file not found:\n{TEST_FILE}"
    )

if not METADATA_FILE.exists():
    raise FileNotFoundError(
        f"Metadata file not found:\n{METADATA_FILE}"
    )


# ============================================================
# CHECK XGBOOST VERSION
# ============================================================

print(f"\nXGBoost version: {xgb.__version__}")

if not hasattr(xgb, "ExtMemQuantileDMatrix"):
    raise RuntimeError(
        "This XGBoost installation does not provide "
        "ExtMemQuantileDMatrix."
    )


# ============================================================
# LOAD METADATA
# ============================================================

with open(
    METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    metadata = json.load(file)


classes = metadata["classes"]
num_classes = len(classes)

print(f"Number of classes: {num_classes}")

print("\nLabel mapping:")

for index, label in enumerate(classes):
    print(f"{index:2d} -> {label}")


# ============================================================
# GET FEATURE NAMES
# ============================================================

print("\nReading training-file header...")

header = pd.read_csv(
    TRAIN_FILE,
    nrows=0
)

feature_columns = [
    column
    for column in header.columns
    if column != "Label"
]

del header
gc.collect()

print(f"Number of features: {len(feature_columns)}")


# ============================================================
# CUSTOM CSV DATA ITERATOR
# ============================================================

class CSVDataIterator(xgb.DataIter):
    """
    Reads the CSV file in small chunks.

    The complete training dataset is NOT loaded into RAM.
    """

    def __init__(
        self,
        csv_file,
        feature_columns,
        chunk_size=100_000,
        cache_prefix=None
    ):

        self.csv_file = str(csv_file)
        self.feature_columns = feature_columns
        self.chunk_size = chunk_size

        self.current_reader = None

        super().__init__(
            cache_prefix=cache_prefix
        )

    def _create_reader(self):

        return pd.read_csv(
            self.csv_file,
            usecols=self.feature_columns + ["Label"],
            chunksize=self.chunk_size,
            low_memory=False
        )

    def next(self, input_data):

        if self.current_reader is None:
            self.current_reader = self._create_reader()

        try:
            chunk = next(self.current_reader)

        except StopIteration:

            self.current_reader = None

            return False

        # ----------------------------------------------------
        # Separate features and labels
        # ----------------------------------------------------

        y = chunk["Label"].to_numpy(
            dtype=np.float32
        )

        X = chunk[self.feature_columns].to_numpy(
            dtype=np.float32
        )

        # ----------------------------------------------------
        # Send this batch to XGBoost
        # ----------------------------------------------------

        input_data(
            data=X,
            label=y
        )

        del chunk
        del X
        del y

        return True

    def reset(self):

        self.current_reader = None


# ============================================================
# REMOVE OLD CACHE
# ============================================================

print("\nPreparing XGBoost cache...")

if CACHE_DIR.exists():

    shutil.rmtree(CACHE_DIR)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CREATE TRAINING ITERATOR
# ============================================================

print("\nCreating training data iterator...")

train_iterator = CSVDataIterator(
    csv_file=TRAIN_FILE,
    feature_columns=feature_columns,
    chunk_size=CHUNK_SIZE,
    cache_prefix=str(
        CACHE_DIR / "train_cache"
    )
)


# ============================================================
# CREATE EXTERNAL-MEMORY D MATRIX
# ============================================================

print("\nCreating external-memory training matrix...")
print("The dataset will be processed in chunks.")

train_matrix = xgb.ExtMemQuantileDMatrix(
    train_iterator,
    missing=np.nan,
    enable_categorical=False
)

print("\nTraining matrix created successfully.")


# ============================================================
# XGBOOST PARAMETERS
# ============================================================

params = {
    "objective": "multi:softprob",

    "num_class": num_classes,

    "tree_method": "hist",

    "max_depth": MAX_DEPTH,

    "learning_rate": LEARNING_RATE,

    "subsample": SUBSAMPLE,

    "colsample_bytree": COLSAMPLE_BYTREE,

    "eval_metric": "mlogloss",

    "seed": RANDOM_STATE,

    "nthread": -1
}


# ============================================================
# TRAIN XGBOOST
# ============================================================

print("\n" + "=" * 70)
print("STARTING XGBOOST TRAINING")
print("=" * 70)

print(f"\nBoosting rounds : {N_ESTIMATORS}")
print(f"Max depth      : {MAX_DEPTH}")
print(f"Learning rate  : {LEARNING_RATE}")
print(f"Training rows  : approximately 2.26 million")
print(f"Batch size     : {CHUNK_SIZE:,}")

print(
    "\nIMPORTANT: Training may take a considerable amount of time."
)

booster = xgb.train(
    params=params,
    dtrain=train_matrix,
    num_boost_round=N_ESTIMATORS,
    verbose_eval=True
)


print("\nXGBoost training completed successfully.")


# ============================================================
# SAVE MODEL
# ============================================================

booster.save_model(
    MODEL_FILE
)

print("\nModel saved to:")
print(MODEL_FILE)


# ============================================================
# RELEASE TRAINING MEMORY
# ============================================================

del train_matrix
del train_iterator

gc.collect()


# ============================================================
# TEST PREDICTIONS
# ============================================================

print("\n" + "=" * 70)
print("EVALUATING MODEL ON TEST DATA")
print("=" * 70)

all_predictions = []
all_true_labels = []

test_reader = pd.read_csv(
    TEST_FILE,
    chunksize=CHUNK_SIZE,
    low_memory=False
)

test_chunk_number = 0

for chunk in test_reader:

    test_chunk_number += 1

    print(
        f"Evaluating test chunk {test_chunk_number}..."
    )

    y_true = chunk["Label"].to_numpy(
        dtype=np.int32
    )

    X_test = chunk[
        feature_columns
    ].to_numpy(
        dtype=np.float32
    )

    test_matrix = xgb.DMatrix(
        X_test,
        feature_names=feature_columns
    )

    probabilities = booster.predict(
        test_matrix
    )

    predictions = np.argmax(
        probabilities,
        axis=1
    )

    all_predictions.extend(
        predictions.tolist()
    )

    all_true_labels.extend(
        y_true.tolist()
    )

    del chunk
    del X_test
    del test_matrix
    del probabilities
    del predictions

    gc.collect()


y_test = np.array(
    all_true_labels,
    dtype=np.int32
)

y_pred = np.array(
    all_predictions,
    dtype=np.int32
)


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n" + "=" * 70)
print("MODEL ACCURACY")
print("=" * 70)

print(
    f"\nAccuracy: {accuracy:.4f}"
)

print(
    f"Accuracy percentage: {accuracy * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

report = classification_report(
    y_test,
    y_pred,
    labels=list(range(num_classes)),
    target_names=classes,
    zero_division=0
)

print("\n")
print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print("=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=list(range(num_classes))
)

print("\n")
print(cm)


# ============================================================
# SAVE METRICS
# ============================================================

report_dict = classification_report(
    y_test,
    y_pred,
    labels=list(range(num_classes)),
    target_names=classes,
    output_dict=True,
    zero_division=0
)

metrics = {

    "accuracy": float(accuracy),

    "accuracy_percentage": float(
        accuracy * 100
    ),

    "classification_report": report_dict,

    "confusion_matrix": cm.tolist(),

    "classes": classes,

    "features": feature_columns,

    "model": {

        "algorithm": "XGBoost",

        "objective": "multi:softprob",

        "tree_method": "hist",

        "n_estimators": N_ESTIMATORS,

        "max_depth": MAX_DEPTH,

        "learning_rate": LEARNING_RATE,

        "subsample": SUBSAMPLE,

        "colsample_bytree": COLSAMPLE_BYTREE,

        "random_state": RANDOM_STATE

    }

}


with open(
    METRICS_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metrics,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("AEGIS ONE XGBOOST TRAINING COMPLETE")
print("=" * 70)

print("\nModel:")
print(MODEL_FILE)

print("\nMetrics:")
print(METRICS_FILE)

print(
    f"\nFinal accuracy: "
    f"{accuracy * 100:.2f}%"
)

print(
    "\nThe Aegis One known-attack classifier "
    "is ready for backend integration."
)
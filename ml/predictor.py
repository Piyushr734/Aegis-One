import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_FILE = (
    BASE_DIR
    / "ml"
    / "models"
    / "aegis_xgboost.json"
)

METRICS_FILE = (
    BASE_DIR
    / "ml"
    / "models"
    / "xgboost_metrics.json"
)

METADATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "cicids2017_metadata.json"
)


# ============================================================
# LOAD MODEL
# ============================================================

if not MODEL_FILE.exists():
    raise FileNotFoundError(
        f"XGBoost model not found:\n{MODEL_FILE}"
    )

print("Loading Aegis One XGBoost model...")

model = xgb.Booster()

model.load_model(MODEL_FILE)

print("XGBoost model loaded successfully.")


# ============================================================
# LOAD METRICS / FEATURE INFORMATION
# ============================================================

if not METRICS_FILE.exists():
    raise FileNotFoundError(
        f"Metrics file not found:\n{METRICS_FILE}"
    )

with open(
    METRICS_FILE,
    "r",
    encoding="utf-8"
) as file:

    metrics = json.load(file)


feature_columns = metrics["features"]


# ============================================================
# LOAD DATASET METADATA
# ============================================================

if not METADATA_FILE.exists():
    raise FileNotFoundError(
        f"Metadata file not found:\n{METADATA_FILE}"
    )

with open(
    METADATA_FILE,
    "r",
    encoding="utf-8"
) as file:

    metadata = json.load(file)


classes = metadata["classes"]

imputation_values = metadata["imputation"]


# ============================================================
# INFORMATION
# ============================================================

print(f"Number of features: {len(feature_columns)}")
print(f"Number of classes : {len(classes)}")

print("\nAegis One attack classes:")

for index, attack in enumerate(classes):
    print(f"{index:2d} -> {attack}")


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_event(event_data: dict):

    """
    Predict the attack type for one network-security event.

    event_data must contain the 78 features used during
    XGBoost training.
    """

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    data = pd.DataFrame([event_data])

    # --------------------------------------------------------
    # Check for missing features
    # --------------------------------------------------------

    missing_features = [
        feature
        for feature in feature_columns
        if feature not in data.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_features)
        )

    # --------------------------------------------------------
    # Keep EXACT feature order used during training
    # --------------------------------------------------------

    data = data[feature_columns]

    # --------------------------------------------------------
    # Convert features to numeric
    # --------------------------------------------------------

    for column in feature_columns:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Apply the SAME median imputation used during training
    # --------------------------------------------------------

    for column, median_value in imputation_values.items():

        if column in data.columns:

            data[column] = data[column].fillna(
                median_value
            )

    # --------------------------------------------------------
    # Convert to float32
    # --------------------------------------------------------

    X = data.to_numpy(
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Create XGBoost DMatrix
    # --------------------------------------------------------

    matrix = xgb.DMatrix(
        X,
        feature_names=feature_columns
    )

    # --------------------------------------------------------
    # Get class probabilities
    # --------------------------------------------------------

    probabilities = model.predict(matrix)

    # --------------------------------------------------------
    # Get predicted class
    # --------------------------------------------------------

    predicted_index = int(
        np.argmax(probabilities[0])
    )

    confidence = float(
        probabilities[0][predicted_index]
    )

    predicted_attack = classes[
        predicted_index
    ]

    # --------------------------------------------------------
    # Create probability dictionary
    # --------------------------------------------------------

    class_probabilities = {}

    for index, attack in enumerate(classes):

        class_probabilities[attack] = float(
            probabilities[0][index]
        )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "predicted_class": predicted_index,
        "attack_type": predicted_attack,
        "confidence": confidence,
        "probabilities": class_probabilities
    }
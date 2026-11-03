import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

# Load deduplicated dataset
data_path = Path("data/processed/food_waste_cleaned.csv")
if not data_path.exists():
    data_path = Path("data/raw/food_waste_dataset.csv")

df = pd.read_csv(data_path)

# Target: Waste_Level ('Low', 'Medium', 'High')
target = "Waste_Level"

features = [
    "Business_Type",
    "Food_Category",
    "Purchase_Quantity",
    "Units_Sold",
    "Remaining_Stock",
    "Shelf_Life_Days",
    "Storage_Temperature",
    "Daily_Demand",
    "Promotion",
    "Weather",
]

categorical_features = [
    "Business_Type",
    "Food_Category",
    "Promotion",
    "Weather",
]

numerical_features = [
    "Purchase_Quantity",
    "Units_Sold",
    "Remaining_Stock",
    "Shelf_Life_Days",
    "Storage_Temperature",
    "Daily_Demand",
]

X = df[features].copy()
y = df[target].copy()

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Preprocessing Pipeline:
# Missing values are imputed STRICTLY on X_train inside ColumnTransformer during model.fit()
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical_features,
        ),
        (
            "numerical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
            ]),
            numerical_features,
        ),
    ]
)

# Full Model Pipeline
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
    )),
])

# Split data: 80% train, 20% test, stratified by target class, reproducible seed 42
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded,
)

# Fit pipeline on training partition only (zero leakage into test partition)
model.fit(X_train, y_train)

# Evaluate on held-out test partition
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
macro_prec = precision_score(y_test, predictions, average="macro", zero_division=0)
macro_rec = recall_score(y_test, predictions, average="macro", zero_division=0)
macro_f1 = f1_score(y_test, predictions, average="macro", zero_division=0)

print("=" * 60)
print("FOOD WASTE LEVEL CLASSIFIER - TRAINING & EVALUATION REPORT")
print("=" * 60)
print(f"Dataset Size: {len(df)} records (Train: {len(X_train)}, Test: {len(X_test)})")
print(f"Data Leakage Safeguard: Preprocessing fitted exclusively on X_train")
print(f"Test Accuracy: {accuracy:.2%}")
print(f"Macro Precision: {macro_prec:.2%}")
print(f"Macro Recall:    {macro_rec:.2%}")
print(f"Macro F1-Score:  {macro_f1:.2%}")
print("\nPer-Class Breakdown:")
print(classification_report(
    y_test,
    predictions,
    labels=range(len(label_encoder.classes_)),
    target_names=label_encoder.classes_,
    zero_division=0,
))
print("=" * 60)

# Save trained pipeline and metadata
output_dir = Path("ml_service/models")
output_dir.mkdir(parents=True, exist_ok=True)

model_artifact_path = output_dir / "waste_level_model.joblib"
joblib.dump(
    {
        "model": model,
        "label_encoder": label_encoder,
        "features": features,
        "categorical_features": categorical_features,
        "numerical_features": numerical_features,
        "metrics": {
            "accuracy": float(accuracy),
            "macro_precision": float(macro_prec),
            "macro_recall": float(macro_rec),
            "macro_f1": float(macro_f1),
        },
    },
    model_artifact_path,
)

print(f"Model artifact saved safely to: {model_artifact_path}")

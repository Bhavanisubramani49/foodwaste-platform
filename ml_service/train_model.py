
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load cleaned dataset
data_path = Path("data/processed/food_waste_cleaned.csv")
df = pd.read_csv(data_path)

# Predict Waste_Level using features available before waste occurs.
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

X = df[features].copy()
y = df[target].copy()

# Encode target labels
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Identify column types
categorical_features = X.select_dtypes(
    include=["object"]
).columns.tolist()

numerical_features = X.select_dtypes(
    exclude=["object"]
).columns.tolist()

# Preprocess data
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

# Build the model
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
    )),
])

# Split data for training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded,
)

# Train
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)

print("Model training completed!")
print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")
print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    labels=range(len(label_encoder.classes_)),
    target_names=label_encoder.classes_,
    zero_division=0,
))

# Save trained model
output_dir = Path("ml_service/models")
output_dir.mkdir(parents=True, exist_ok=True)

joblib.dump(
    {"model": model, "label_encoder": label_encoder, "features": features},
    output_dir / "waste_level_model.joblib",
)

print("\nModel saved to ml_service/models/waste_level_model.joblib")

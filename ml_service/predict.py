
import joblib
import pandas as pd
from pathlib import Path

model_path = Path("ml_service/models/waste_level_model.joblib")

# Load trained model
saved = joblib.load(model_path)
model = saved["model"]
label_encoder = saved["label_encoder"]
features = saved["features"]

# Sample inventory details
sample = {
    "Business_Type": "Restaurant",
    "Food_Category": "Vegetables",
    "Purchase_Quantity": 100,
    "Units_Sold": 65,
    "Remaining_Stock": 35,
    "Shelf_Life_Days": 2,
    "Storage_Temperature": 25,
    "Daily_Demand": 70,
    "Promotion": "No",
    "Weather": "Hot",
}

# Convert input into a DataFrame
input_data = pd.DataFrame([sample], columns=features)

# Predict waste level
prediction = model.predict(input_data)[0]
waste_level = label_encoder.inverse_transform([prediction])[0]

print("Food Waste Level Prediction:", waste_level)

# Display prediction probabilities
probabilities = model.predict_proba(input_data)[0]

print("\nPrediction probabilities:")
for level, probability in zip(label_encoder.classes_, probabilities):
    print(f"{level}: {probability:.2%}")

import pandas as pd
from pathlib import Path

# File paths
input_path = Path("data/raw/food_waste_dataset.csv")
output_path = Path("data/processed/food_waste_cleaned.csv")

# Load raw dataset
df = pd.read_csv(input_path)

# Remove duplicate records
df = df.drop_duplicates()

# Note: Missing values are intentionally preserved here to prevent data leakage.
# Imputation must be fitted strictly on the training partition inside the scikit-learn Pipeline.

# Create output directory
output_path.parent.mkdir(parents=True, exist_ok=True)

# Save cleaned dataset
df.to_csv(output_path, index=False)

print("Data cleaning completed (duplicates removed, no data leakage)!")
print("Dataset shape:", df.shape)
print("Missing values preserved for pipeline imputation:\n", df.isnull().sum()[df.isnull().sum() > 0])
print("Saved to:", output_path)

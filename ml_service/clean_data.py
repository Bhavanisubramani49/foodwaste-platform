
import pandas as pd
from pathlib import Path

# File paths
input_path = Path("data/raw/food_waste_dataset.csv")
output_path = Path("data/processed/food_waste_cleaned.csv")

# Load dataset
df = pd.read_csv(input_path)

# Remove duplicate records
df = df.drop_duplicates()

# Fill missing numerical values with median
numerical_columns = [
    "Shelf_Life_Days",
    "Storage_Temperature",
    "Daily_Demand",
]

for column in numerical_columns:
    df[column] = df[column].fillna(df[column].median())

# Fill missing categorical values with most frequent value
categorical_columns = ["Weather", "Donation_Made"]

for column in categorical_columns:
    df[column] = df[column].fillna(df[column].mode()[0])

# Create output directory
output_path.parent.mkdir(parents=True, exist_ok=True)

# Save cleaned dataset
df.to_csv(output_path, index=False)

print("Data cleaning completed!")
print("Dataset shape:", df.shape)
print("Remaining missing values:", df.isnull().sum().sum())
print("Saved to:", output_path)

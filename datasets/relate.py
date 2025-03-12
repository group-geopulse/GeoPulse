import pandas as pd

# Load the CSV files into DataFrames
wti_df = pd.read_csv("wti_brent_crude_oil_prices_preprocessed.csv")
gdelt_df = pd.read_csv("gdelt_5_years_filtered_preprocessed.csv")

# Convert the '_id' column in wti_df and 'Date' column in gdelt_df to datetime
wti_df['_id'] = pd.to_datetime(wti_df['_id'])
gdelt_df['Date'] = pd.to_datetime(gdelt_df['Date'])

print(wti_df.shape)
print(gdelt_df.shape)

# Ensure the 'Date' in gdelt_df matches the '_id' in wti_df
# This step assumes that the 'Date' in gdelt_df is already correct and matches the '_id' in wti_df

# Create a new DataFrame that relates the Headline in GDELT data to the Date in WTI data
relation_df = gdelt_df[['Headline', 'Date']].drop_duplicates()

print(relation_df.shape)

# Convert 'Date' to string format for better readability
relation_df['Date'] = relation_df['Date'].dt.strftime('%Y-%m-%d')

# Save the new DataFrame to a CSV file
relation_df.to_csv("gdelt_wti_headline_date_relation.csv", index=False)

# Print the first few rows of the new DataFrame
print("First few rows of the relation DataFrame:")
print(relation_df.head())
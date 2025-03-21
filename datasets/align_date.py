import pandas as pd

# Load the CSV files into DataFrames
wti_df = pd.read_csv("wti_brent_crude_oil_prices_preprocessed.csv")
gdelt_df = pd.read_csv("gdelt_5_years_filtered_preprocessed.csv")

# Convert the '_id' column in wti_df and 'Date' column in gdelt_df to datetime
wti_df['_id'] = pd.to_datetime(wti_df['_id'])
gdelt_df['Date'] = pd.to_datetime(gdelt_df['Date'])

# Get the list of dates in wti_df
wti_dates = wti_df['_id'].sort_values().unique()

# Get the list of dates in gdelt_df
gdelt_dates = gdelt_df['Date'].sort_values().unique()

# Find the missing dates in wti_df
missing_dates = [date for date in gdelt_dates if date not in wti_dates]
print("Missing dates in WTI data:", missing_dates)

# Function to find the next available date in wti_dates
def get_next_available_date(date):
    for wti_date in wti_dates:
        if wti_date >= date:
            return wti_date
    return None

# Update the dates in gdelt_df
gdelt_df['Updated_Date'] = gdelt_df['Date'].apply(get_next_available_date)

# Drop rows where Updated_Date is None (no next available date found)
gdelt_df = gdelt_df.dropna(subset=['Updated_Date'])

# Save the updated gdelt_df to a new CSV file
gdelt_df.to_csv("gdelt_5_years_filtered_updated.csv", index=False)

# Confirm that all dates in the updated gdelt_df are present in wti_df
updated_gdelt_dates = gdelt_df['Updated_Date'].sort_values().unique()
missing_after_update = [date for date in updated_gdelt_dates if date not in wti_dates]
print("Dates in GDELT data missing in WTI data after update:", missing_after_update)
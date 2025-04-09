import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

# Define the crude oil ticker symbols
symbols = ['CL=F', 'BZ=F']

# Define the start and end dates
start_date = "2020-01-01"
end_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')  # Tomorrow's date

# Fetch historical data
data = yf.download(symbols, start=start_date, end=end_date, interval="1d")

# Select only the required columns
filtered_data = data[['Open', 'Close']]
filtered_data.columns = ['CL=F Open', 'BZ=F Open', 'CL=F Close', 'BZ=F Close']

# Reset index to make Date a column and change date format
filtered_data = filtered_data.reset_index()
filtered_data['Date'] = filtered_data['Date'].dt.strftime('%Y-%m-%d')

# Calculate percentage change from the previous day
filtered_data['CL=F Daily % Change'] = filtered_data['CL=F Close'].pct_change().fillna(0) * 100
filtered_data['BZ=F Daily % Change'] = filtered_data['BZ=F Close'].pct_change().fillna(0) * 100

# Calculate percentage change from the previous week (7 prices ago)
filtered_data['CL=F Weekly % Change'] = filtered_data['CL=F Close'].pct_change(periods=7).fillna(0) * 100
filtered_data['BZ=F Weekly % Change'] = filtered_data['BZ=F Close'].pct_change(periods=7).fillna(0) * 100

# Define the path to save the file
file_path = os.path.expanduser('wti_brent_crude_oil_prices_1Jan2020_25March2025_with_delta.csv')

# Display first few rows
print(filtered_data.head())

# Save to CSV
filtered_data.to_csv(file_path, index=False)
print(f"Data saved to {file_path}")

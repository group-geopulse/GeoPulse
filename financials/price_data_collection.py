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
filtered_data['Date'] = filtered_data['Date'].dt.strftime('%d-%m-%Y')

# Define the path to save the file
file_path = os.path.expanduser('wti_brent_crude_oil_prices.csv')

# Display first few rows
print(filtered_data.head())

# Save to CSV
filtered_data.to_csv(file_path, index=False)
print(f"Data saved to {file_path}")

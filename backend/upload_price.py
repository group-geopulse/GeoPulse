import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from mongodb_utils import upload_to_mongodb

# Define the crude oil ticker symbols
symbols = ['CL=F', 'BZ=F']

# Define the start and end dates
start_date = datetime.now().strftime('%Y-%m-%d')
end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# Fetch historical data
data = yf.download(symbols, start=start_date, end=end_date, interval="1d")

# Select only the required columns
filtered_data = data[['Open', 'Close']]
filtered_data.columns = ['CL=F Open', 'BZ=F Open', 'CL=F Close', 'BZ=F Close']

# Reset index to make Date a column and change date format
filtered_data = filtered_data.reset_index()
filtered_data['Date'] = filtered_data['Date'].dt.strftime('%Y-%m-%d')
filtered_data.rename(columns={'Date': '_id'}, inplace=True)

# Convert DataFrame to dictionary
data_dict = filtered_data.to_dict(orient="records")

# Upload data to MongoDB
upload_to_mongodb(data_dict, db_name="YfinancePrices", collection_name="Prices")
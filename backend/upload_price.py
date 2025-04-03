import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from mongodb_utils import upload_to_mongodb, get_recent_records
from kg_updating import update_oilprice_nodes
import logging

# Set up logging
logging.basicConfig(filename='upload_price.log', level=logging.INFO, format='%(asctime)s %(message)s')

logging.info('Starting upload_price.py script')

try:
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

    # Query the last 7 records from MongoDB
    recent_records = get_recent_records(db_name="ProdPricesDB", collection_name="Prices", limit=8)

    # Combine recent records with the new data
    if not recent_records.empty:
        # Sort recent records by `_id` (Date) in ascending order
        recent_records = recent_records.sort_values(by="_id")

        # Append the new data to the recent records for calculation
        combined_data = pd.concat([recent_records, filtered_data], ignore_index=True)

        # Calculate daily percentage change
        combined_data['CL=F Daily % Change'] = combined_data['CL=F Close'].pct_change().fillna(0) * 100
        combined_data['BZ=F Daily % Change'] = combined_data['BZ=F Close'].pct_change().fillna(0) * 100

        # Calculate weekly percentage change (7 records ago)
        combined_data['CL=F Weekly % Change'] = combined_data['CL=F Close'].pct_change(periods=7).fillna(0) * 100
        combined_data['BZ=F Weekly % Change'] = combined_data['BZ=F Close'].pct_change(periods=7).fillna(0) * 100

        # Keep only the new data (last row(s) from `filtered_data`)
        filtered_data = combined_data.iloc[-len(filtered_data):]

    else:
        # If no recent records exist, initialize percentage changes to 0
        filtered_data['CL=F Daily % Change'] = 0
        filtered_data['BZ=F Daily % Change'] = 0
        filtered_data['CL=F Weekly % Change'] = 0
        filtered_data['BZ=F Weekly % Change'] = 0

    # Convert DataFrame to dictionary
    data_dict = filtered_data.to_dict(orient="records")

    # Upload data to MongoDB
    upload_to_mongodb(data_dict, db_name="ProdPricesDB", collection_name="Prices")
    upload_to_mongodb(data_dict, db_name="ProdPricesDB", collection_name="StagingPrices")

    logging.info('Successfully uploaded price data to both MongoDB collections (Prices and StagingPrices).')
    logging.info(f'Uploaded data: {data_dict}')

    # Upload data as nodes to KG
    # SWITCH FOR PRODUCTION
    logging.info(update_oilprice_nodes("ProdPricesDB", "StagingPricesTEST", use_testKG=True))
    # logging.info(update_oilprice_nodes("ProdPricesDB", "StagingPrices", use_testKG=False))    

except Exception as e:
    logging.error(f'Error in upload_price.py: {e}')
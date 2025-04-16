import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse
from mongodb_utils import get_existing_dates_from_mongodb
import re
import os
from news_processing import get_next_available_date
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get MongoDB connection URI from environment variable
URI = os.getenv("URI")

def extract_date_from_snippet(snippet):
    today = datetime.today()
    date_pattern = r'([A-Za-z]{3} \d{1,2}, \d{4})'
    days_ago_pattern = r'(\d+) day[s]? ago'
    hours_ago_pattern = r'(\d+) hour[s]? ago'

    match = re.search(date_pattern, snippet)
    if match:
        try:
            return datetime.strptime(match.group(), "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            return today.strftime("%Y-%m-%d")

    match = re.search(days_ago_pattern, snippet)
    if match:
        days_ago = int(match.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    match = re.search(hours_ago_pattern, snippet)
    if match:
        return today.strftime("%Y-%m-%d")

    return today.strftime("%Y-%m-%d")

def fix_dates(articles, existing_dates):
    """Fix dates in the articles DataFrame."""

    # Convert 'Date' to a standardized format (YYYY-MM-DD)    
    articles['Date'] = articles['Original_Date'].apply(lambda x: extract_date_from_snippet(x) if isinstance(x, str) else None)    

    # Step 3: Calculate 'Updated_Date' based on the next available date
    articles['Updated_Date'] = pd.to_datetime(articles['Date']).apply(lambda x: get_next_available_date(x, existing_dates))

    # Step 4: Drop rows where 'Updated_Date' is None (invalid or missing dates)
    articles = articles.dropna(subset=['Updated_Date'])

    # Step 5: Convert 'Updated_Date' back to string format
    articles['Updated_Date'] = articles['Updated_Date'].dt.strftime('%Y-%m-%d')
    
    # Select the required columns and rename them
    articles = articles[['Original_Date', 'Date', 'Updated_Date', 'Headline', 'Link', 'Description', 'Author', 'Full_info', 'Locations', 'Organizations', 'People', 'Topics', 'Events']]

    return articles

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename='process_prod_prices.log', level=logging.INFO, format='%(asctime)s %(message)s')

    # Fetch existing dates from the price database
    existing_dates = get_existing_dates_from_mongodb(db_name="ProdPricesDB", collection_name="Prices", uri=URI)

    if existing_dates is None:
        logging.error("Failed to fetch existing dates from MongoDB.")
        exit(1)
        
    # Load opinions data from CSV
    opinions_data = pd.read_csv("oil_opinions.csv", engine="python", quoting=1)
    if opinions_data.empty:
        logging.warning("No data found in the CSV file.")
        exit(1)
        
    opinions_data = opinions_data.applymap(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x)

    # fix the dates in the opinions data usng fix_dates function
    opinions_data = fix_dates(opinions_data, existing_dates)
    
    if opinions_data.empty:
        logging.warning("No valid data found after fixing dates.")
        exit(1)
        
    # Check columns date, udpated_Date and oroiginal date exist
    if not all(col in opinions_data.columns for col in ['Date', 'Updated_Date', 'Original_Date']):
        logging.error("Missing required columns in the DataFrame.")
        exit(1)
        
    # Save the processed data to a new CSV file
    output_file = "processed_opinions.csv"
    opinions_data.to_csv(output_file, index=False)
    logging.info(f"Processed data saved to {output_file}.")
    
    

import gdeltdoc
from gdeltdoc import Filters
from datetime import datetime, timedelta
import pandas as pd
from mongodb_utils import upload_to_mongodb, get_existing_dates_from_mongodb
from news_processing import fetch_real_time_news, process_articles
import logging

# api credentials
API_KEY = "AIzaSyD9IvPQAHwQMLVfiAv2CxgKZpR9-yWGhMI" # "AIzaSyCH6MfgENpREBBEtbM-h0IbpNyPK_G5_CE"
SEARCH_ENGINE_ID = "127bf9dbecbe84e04" # "707f9db5f58494409"

# news sources
sources = ["bloomberg.com", "ft.com", "reuters.com"]

# keywords
keywords = ("tensions OR crude OR oil prices OR oil supply OR disruption OR brent OR "
            "sanctions OR embargo OR OPEC OR Middle East OR Russia OR Ukraine OR petroleum OR "
            "fuel OR energy OR climate OR global warming OR conflict OR war OR economy OR inflation")

API_REQUEST_LIMIT = 100

# Set up logging
logging.basicConfig(filename='upload_news.log', level=logging.INFO, format='%(asctime)s %(message)s')

logging.info('Starting upload_news.py script')

try:
    
    # Fetch existing dates from the price database
    existing_dates = get_existing_dates_from_mongodb(db_name="YfinancePrices", collection_name="Prices")
    
    # # Define the date range (Getting yesterday's articles)
    # yesterday = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    # day_before_yesterday = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')

    # # Define the filters
    # f = Filters(
    #     start_date=day_before_yesterday,
    #     end_date=yesterday,
    #     domain=['bloomberg.com', 'reuters.com']
    # )

    # # Fetch GDELT data
    # gd = gdeltdoc.GdeltDoc()
    # articles = gd.article_search(f)
    
    # # Convert to DataFrame
    # articles = pd.DataFrame(articles)

    # # Process articles to fix dates and filter by keywords
    # articles = process_articles(articles, existing_dates)
    # articles.to_csv("trial.csv", index=False)
    
    # # Convert DataFrame to dictionary
    # data_dict = articles.to_dict(orient="records")

    # # Upload data to MongoDB
    # upload_to_mongodb(data_dict, db_name="GDELTNews", collection_name="News")
    # logging.info('Successfully uploaded historical news data to MongoDB')

    API_KEY = "AIzaSyD9IvPQAHwQMLVfiAv2CxgKZpR9-yWGhMI" # "AIzaSyCH6MfgENpREBBEtbM-h0IbpNyPK_G5_CE"
    SEARCH_ENGINE_ID = "127bf9dbecbe84e04" # "707f9db5f58494409"    

    real_time_news = fetch_real_time_news(API_KEY, SEARCH_ENGINE_ID, sources, keywords, API_REQUEST_LIMIT)
    real_time_news = pd.DataFrame(real_time_news)
    print(real_time_news.head())
    real_time_news.to_csv("initial.csv", index=False)
    processed_real_time_news = process_articles(real_time_news, existing_dates)

    # data_dict = processed_real_time_news.to_dict(orient="records")
    # upload_to_mongodb(data_dict, "RealTimeNews", "News")
    # logging.info("Real-time news uploaded successfully")
    
except Exception as e:
    logging.error(f'Error in upload_news.py: {e}')


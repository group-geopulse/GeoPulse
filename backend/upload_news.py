import gdeltdoc
from gdeltdoc import Filters
from datetime import datetime, timedelta
import pandas as pd
from mongodb_utils import upload_to_mongodb, get_existing_dates_from_mongodb
from news_processing import process_articles

# Fetch existing dates from the price database
existing_dates = get_existing_dates_from_mongodb(db_name="YfinancePrices", collection_name="Prices")

# Define the date range (Getting yesterday's articles)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
day_before_yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')

# Define the filters
f = Filters(
    start_date=day_before_yesterday,
    end_date=yesterday,
    domain=['bloomberg.com', 'reuters.com']
)

# Fetch GDELT data
gd = gdeltdoc.GdeltDoc()
articles = gd.article_search(f)

# Convert to DataFrame
articles = pd.DataFrame(articles)

# Process articles to fix dates and filter by keywords
articles = process_articles(articles, existing_dates)

# Convert DataFrame to dictionary
data_dict = articles.to_dict(orient="records")

# Upload data to MongoDB
upload_to_mongodb(data_dict, db_name="GDELTNews", collection_name="News")
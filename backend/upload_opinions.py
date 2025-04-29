from datetime import datetime, timedelta
import pandas as pd
from mongodb_utils import upload_to_mongodb, get_existing_dates_from_mongodb
from news_processing import process_opinions
from opinions import scrape_headlines
from kg_updating import update_entity_db_and_nodes, update_article_nodes
import logging
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get MongoDB connection URI from environment variable
URI = os.getenv("URI")

# Set up logging
logging.basicConfig(filename='upload_opinions.log', level=logging.INFO, format='%(asctime)s %(message)s')

logging.info('Starting upload_opinions.py script')
print('Starting upload_opinions.py script')

try:
    
    # Fetch existing dates from the price database
    existing_dates = get_existing_dates_from_mongodb(db_name="ProdPricesDB", collection_name="Prices", uri=URI)
    print(f"Existing dates from MongoDB")    

    real_time_opinions = scrape_headlines()
    real_time_opinions = pd.DataFrame(real_time_opinions)
    print(f"Opinions fetched.")
    
    if real_time_opinions.empty:
        # No new opinions at datetme.now()
        print(f"No new opinions to process at {datetime.now()}.")
        logging.info(f"No new opinions to process today at {datetime.now()}.")
        exit(0)
    
    processed_real_time_opinions = process_opinions(real_time_opinions, existing_dates)
    logging.info(f"Number of Opinions after processing today: {len(processed_real_time_opinions)}")
    print(f"Opinions processed.")
    print(processed_real_time_opinions.head())
    
    # Save to file for testing
    processed_real_time_opinions.to_csv("processed_real_time_opinions.csv", index=False)
    
    data_dict = processed_real_time_opinions.to_dict(orient="records")
    
    # Testing Data Upload: Upload to testing db
    # THIS HAS NOT BEEN ADAPTED FOR OPINIONS, PLS DO THAT, DO NOT JUST UNCOMMENT
    #upload_to_mongodb(data=data_dict, db_name="GDELTNews", collection_name="News", uri=URI)
    
    # Testing Entities: process entity records to update/create new nodes in KG
    # entity_cols_test = {"Locations": "LocationsTEST", "Organizations": "OrganizationsTEST", "People": "PeopleTEST", "Topics": "TopicsTEST", "Events": "EventsTEST"}
    # print(update_entity_db_and_nodes("RealTimeNews", "Entities", "StagingNewsTEST", entity_cols_test, use_testKG=True))

    # Testing: process news records and add nodes to KG
    # print(update_news_nodes("RealTimeNews", "StagingNewsTEST", use_testKG=True))
    
    # Production Data Upload: Upload to production db
    # Add to daily news db for updating KG
    upload_to_mongodb(data=data_dict, db_name="ProdOpinionDB", collection_name="Opinions", uri=URI)
    # Sending to complete news db
    upload_to_mongodb(data=data_dict, db_name="ProdOpinionDB", collection_name="StagingOpinions", uri=URI)

    logging.info('Successfully uploaded real-time opinions data to MongoDB.')
    print(f"Opinions uploaded to MongoDB at {datetime.now()}.")

    # Production Entities: process entity records to update/create new nodes in KG
    # Update entity collections and create/update entity nodes in knowledge graph
    entity_cols = {"Locations": "Locations", "Organizations": "Organizations", "People": "People", "Topics": "Topics", "Events": "Events"}
    logging.info(update_entity_db_and_nodes("ProdOpinionDB", "Entities", "StagingOpinions", entity_cols, use_testKG=False))

    # Create daily article nodes on KG with relationships and clear 'StagingOpinions'
    logging.info(update_article_nodes("ProdOpinionDB", "StagingOpinions", use_testKG=False))
    logging.info("Real-time opinion task completed successfully!")
    
except Exception as e:
    logging.error(f'Error in upload_opinions.py: {e}')
    print(f"Error in upload_opinions.py: {e}")


import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

# MongoDB connection details
URI = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"

def get_mongo_client(uri=URI):
    """Create a MongoDB client connection."""
    return MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

def upload_to_mongodb(data, db_name, collection_name, uri=URI):
    """Upload data to MongoDB."""
    client = get_mongo_client(uri)
    db = client[db_name]
    collection = db[collection_name]
    
    try:
        collection.insert_many(data)
        print(f"Data successfully uploaded to MongoDB collection '{collection_name}' in database '{db_name}'.")
    except Exception as e:
        print("Error uploading data:", e)
    finally:
        client.close()
        
def get_existing_dates_from_mongodb(db_name, collection_name, uri=URI):
    """Fetch existing dates from the specified collection in MongoDB."""
    client = get_mongo_client(uri)
    db = client[db_name]
    collection = db[collection_name]
    dates = collection.distinct('_id')
    client.close()
    return sorted(pd.to_datetime(dates))
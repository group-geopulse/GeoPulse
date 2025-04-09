import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

# MongoDB connection details
#URI = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"
URI = os.getenv("URI")

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

def get_recent_records(db_name, collection_name, limit=7, uri=URI):
    """Fetch the most recent records from the specified collection in MongoDB."""
    client = get_mongo_client(uri)
    db = client[db_name]
    collection = db[collection_name]
    
    try:
        # Fetch the most recent `limit` records sorted by `_id` (Date)
        recent_records = list(collection.find().sort("_id", -1).limit(limit))
        return pd.DataFrame(recent_records)  # Convert to DataFrame for easier processing
    except Exception as e:
        print(f"Error fetching recent records: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error
    finally:
        client.close()
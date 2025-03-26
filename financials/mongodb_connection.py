from pymongo import MongoClient
from pymongo.server_api import ServerApi

def get_mongo_client(uri=None, mock_client=None):

    if mock_client:
        return mock_client  # Use mock client for testing

    if uri is None:
        uri = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"

    return MongoClient(uri, server_api=ServerApi('1'))

if __name__ == "__main__":
    client = get_mongo_client()
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"Connection failed: {e}")

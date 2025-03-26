import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection details
uri = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"

# Create a client connection
client = MongoClient(uri, server_api=ServerApi('1'))

# Select database
db = client["Entities"]
entities = ["locations", "organizations", "topics", "people", "events"]

for entity in entities:
    # Select collections
    collection = db[entity.title()] 

    # Load CSV data
    csv_file_path = f"20_25_{entity}.csv"
    df = pd.read_csv(csv_file_path)

    # Convert DataFrame to dictionary
    data = df.to_dict(orient="records")

    # Insert data into MongoDB
    try:
        collection.insert_many(data)
        print("CSV data successfully uploaded to MongoDB.")
    except Exception as e:
        print("Error uploading data:", e)

# Close the connection
client.close()

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
keys = {"locations": "Location", "organizations": "Organization", "topics": "Topic", "people": "Person", "events": "Event"}

for entity in entities:
    # Select collections
    collection = db[entity.title()] 

    # Load CSV data
    csv_file_path = f"20_25_{entity}.csv"
    df = pd.read_csv(csv_file_path)

    # Convert DataFrame to dictionary
    data = df.to_dict(orient="records")

    try:
        # Insert data into MongoDB
        collection.delete_many({})  # Clear existing data
        # Insert new data
        collection.insert_many(data)

        # Identify duplicates (ignoring _id) and keep only one
        pipeline = [
            {"$group": {
                "_id": {
                    f"{keys[entity]}": f"${keys[entity]}",
                    "Count": "$Count"
                },
                "dupes": {"$addToSet": "$_id"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}  # Only keep duplicates
        ]        

        duplicates = collection.aggregate(pipeline)

        # Delete duplicate documents (keeping only one)
        for doc in duplicates:
            dup_ids = doc["dupes"]
            dup_ids.pop(0)  # Keep one and delete the rest
            collection.delete_many({"_id": {"$in": dup_ids}})

    except Exception as e:
        print("Error uploading data:", e)
    
    print(f"CSV data successfully uploaded to MongoDB for {entity}.")

# Close the connection
client.close()

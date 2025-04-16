import pandas as pd
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection details
uri = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"

# Create a client connection
client = MongoClient(uri, server_api=ServerApi('1'))

# Select database and collection
db = client["ProdNewsDB"] 
collection = db["News"] 

# Load CSV data
csv_file_path = "gdelt_5_years_with_keyword_sentiment_updated.csv"  
df = pd.read_csv(csv_file_path)

# Convert DataFrame to dictionary
data = df.to_dict(orient="records")

# Insert data into MongoDB
try:
    collection.delete_many({})  # Clear existing data
    collection.insert_many(data)
    print("Latest CSV data successfully uploaded to MongoDB.")
except Exception as e:
    print("Error uploading data:", e)

# Close the connection
client.close()

import requests
import re
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# api credentials
API_KEY = "AIzaSyD9IvPQAHwQMLVfiAv2CxgKZpR9-yWGhMI" # "AIzaSyCH6MfgENpREBBEtbM-h0IbpNyPK_G5_CE"
SEARCH_ENGINE_ID = "127bf9dbecbe84e04" # "707f9db5f58494409"

# md connection details
uri = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["RealTime"]
collection = db["News"]

# news sources
sources = ["bloomberg.com", "ft.com", "reuters.com"]

# keywords
keywords = ("tensions OR crude OR oil prices OR oil supply OR disruption OR brent OR "
            "sanctions OR embargo OR OPEC OR Middle East OR Russia OR Ukraine OR petroleum OR "
            "fuel OR energy OR climate OR global warming OR conflict OR war OR economy OR inflation")

# api request limit
API_REQUEST_LIMIT = 100

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
            return None
    
    match = re.search(days_ago_pattern, snippet)
    if match:
        days_ago = int(match.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    match = re.search(hours_ago_pattern, snippet)
    if match:
        return today.strftime("%Y-%m-%d")
    
    return None

def extract_source(url):
    
    domain = urlparse(url).netloc

    return domain.replace("www.", "") if domain else "Unknown"

def load_existing_headlines():
    
    existing_headlines = set()
    for doc in collection.find({}, {"Headline": 1}):
        if "Headline" in doc:
            existing_headlines.add(doc["Headline"].lower())
    return existing_headlines

def fetch_headlines():
    data = []
    existing_headlines = load_existing_headlines()
    request_count = 0  

    for site in sources:
        for start in range(1, 51, 10):  
            if request_count >= API_REQUEST_LIMIT:
                print("API request limit reached. Stopping further queries.")
                return data
            
            query = f"({keywords.replace(' OR ', ' | ')}) site:{site}"
            url = (f"https://www.googleapis.com/customsearch/v1?"
                   f"q={query}&cx={SEARCH_ENGINE_ID}&key={API_KEY}"
                   f"&gl=us&hl=en&sort=date&start={start}"
                   f"&dateRestrict=d1")  

            print(f"Querying: {url}")
            request_count += 1  

            try:
                response = requests.get(url)
                response.raise_for_status()
                result = response.json()

                items = result.get('items', [])
                if not items:
                    print(f"No results found on page {start} for {site}. Stopping pagination.")
                    break

                for item in items:
                    headline = item.get('title', 'No Title').strip()
                    link = item.get('link', 'No Link')
                    snippet = item.get('snippet', 'No Snippet')
                    source = extract_source(link)
                    extracted_date = extract_date_from_snippet(snippet)

                    if headline.lower() in existing_headlines:
                        continue  

                    data.append({
                        "Headline": headline,
                        "Link": link,
                        "Source": source,
                        "Snippet": snippet,
                        "Date": extracted_date if extracted_date else "Unknown",
                        "Tone": "",
                        "Positive Score": "",
                        "Negative Score": "",
                        "Polarity": ""
                    })

            except requests.exceptions.RequestException as e:
                print(f"Error fetching results from {site}: {e}")
                continue

    return data

def save_to_mongo(new_data):
    
    if new_data:
        try:
            collection.insert_many(new_data)
            print(f"{len(new_data)} new headlines added to MongoDB.")
        except Exception as e:
            print("Error inserting data into MongoDB:", e)
    else:
        print("No new headlines found.")

if __name__ == "__main__":
    new_headlines = fetch_headlines()
    save_to_mongo(new_headlines)
    client.close()

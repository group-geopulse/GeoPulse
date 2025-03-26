import requests
import re
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse

# API credentials
API_KEY = "AIzaSyD9IvPQAHwQMLVfiAv2CxgKZpR9-yWGhMI" # "AIzaSyCH6MfgENpREBBEtbM-h0IbpNyPK_G5_CE"
SEARCH_ENGINE_ID = "127bf9dbecbe84e04" # "707f9db5f58494409"

# news sources
sources = ["bloomberg.com", "ft.com", "reuters.com"]

# keywords
keywords = ("tensions OR crude OR oil prices OR oil supply OR disruption OR brent OR "
            "sanctions OR embargo OR OPEC OR Middle East OR Russia OR Ukraine OR petroleum OR "
            "fuel OR energy OR climate OR global warming OR conflict OR war OR economy OR inflation")

csv_file = "real_time_headlines.csv"


def extract_date_from_snippet(snippet):
    
    today = datetime.today()
    date_pattern = r'([A-Za-z]{3} \d{1,2}, \d{4})'
    days_ago_pattern = r'(\d+) day[s]? ago'
    hours_ago_pattern = r'(\d+) hour[s]? ago'
    
    # check for absolute date format
    match = re.search(date_pattern, snippet)
    if match:
        try:
            return datetime.strptime(match.group(), "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            return None
    
    # check for 'X days ago'
    match = re.search(days_ago_pattern, snippet)
    if match:
        days_ago = int(match.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # check for 'X hours ago'
    match = re.search(hours_ago_pattern, snippet)
    if match:
        return today.strftime("%Y-%m-%d")
    
    return None


def extract_source(url):
    """Extracts the domain name from a given URL (e.g., 'bloomberg.com')."""
    domain = urlparse(url).netloc


    return domain.replace("www.", "") if domain else "Unknown"


def load_existing_headlines(file_path):
    """Loads existing headlines from CSV to prevent duplicates."""
    try:
        existing_df = pd.read_csv(file_path)
        return set(existing_df["Headline"].dropna().str.lower())

    except FileNotFoundError:
        return set()


def fetch_headlines():
    data = []
    existing_headlines = load_existing_headlines(csv_file)  # load existing headlines to avoid duplicates

    for site in sources:
        for start in range(1, 51, 10):  # pagination: 10 results per page
            query = f"({keywords.replace(' OR ', ' | ')}) site:{site}"
            url = (f"https://www.googleapis.com/customsearch/v1?"
                   f"q={query}&cx={SEARCH_ENGINE_ID}&key={API_KEY}"
                   f"&gl=us&hl=en&sort=date&start={start}"
                   f"&dateRestrict=d1")  # d1 restricts to last 24 hours

            print(f"Querying: {url}")

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

                    # duplicates
                    if headline.lower() in existing_headlines:
                        continue  

                    # Append new data
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


def save_to_csv(new_data):
   
    df = pd.DataFrame(new_data)

    if not df.empty:
        try:
            existing_df = pd.read_csv(csv_file)
            combined_df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset=["Headline"])
        except FileNotFoundError:
            combined_df = df  # if file doesn't exist, just save new data

        combined_df.to_csv(csv_file, index=False)
        print(f"{len(new_data)} new headlines appended to '{csv_file}'. Total: {len(combined_df)} headlines.")
    else:
        print("No new headlines found.")


if __name__ == "__main__":
    new_headlines = fetch_headlines()
    save_to_csv(new_headlines)

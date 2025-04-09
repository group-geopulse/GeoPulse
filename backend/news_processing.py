from transformers import pipeline
import pandas as pd
import requests
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

def get_next_available_date(date, existing_dates):
    """Find the next available date in existing_dates."""
    """Find the next available date in existing_dates.
    If today's date is not available, return the closest previous date."""
    # Check for the closest previous date
    closest_previous_date = None
    for existing_date in existing_dates:
        if existing_date == date:
            return existing_date  # Return today's date if it exists
        elif existing_date < date:
            closest_previous_date = existing_date  # Update closest previous date

    # If today's date is not found, return the closest previous date
    return closest_previous_date

def fix_dates(articles, existing_dates):
    """Fix dates in the articles DataFrame."""
    # Step 1: Preserve the original 'Date' column as 'Original_Date'
    articles['Original_Date'] = articles['Date']

    # Step 2: Convert 'Date' to a standardized format (YYYY-MM-DD)
    articles['Date'] = pd.to_datetime(articles['Date']).dt.strftime('%Y-%m-%d')

    # Step 3: Calculate 'Updated_Date' based on the next available date
    articles['Updated_Date'] = pd.to_datetime(articles['Date']).apply(lambda x: get_next_available_date(x, existing_dates))

    # Step 4: Drop rows where 'Updated_Date' is None (invalid or missing dates)
    articles = articles.dropna(subset=['Updated_Date'])

    # Step 5: Convert 'Updated_Date' back to string format
    articles['Updated_Date'] = articles['Updated_Date'].dt.strftime('%Y-%m-%d')
    
    # Select the required columns and rename them
    articles = articles[['Original_Date', 'Source', 'Headline', 'Link', 'Snippet', 'Date', 'Updated_Date' ]]

    return articles

# Sentiment analysis functions
# Load FinSentGPT model
sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")

# Domain-specific keywords
positive_keywords = ['increase', 'growth', 'boost', 'profit', 'rise', 'gain', 'stable']
negative_keywords = ['tensions', 'disruption', 'sanctions', 'embargo', 'decline', 'drop', 'crisis', 'loss']

def count_keywords(text, keyword_list):
    return sum(1 for keyword in keyword_list if keyword.lower() in text.lower())

def adjust_sentiment_score(result, text):
    label = result["label"].lower()
    score = result["score"]

    pos_count = count_keywords(text, positive_keywords)
    neg_count = count_keywords(text, negative_keywords)

    if pos_count > neg_count:
        if label == "negative":
            score = max(0.01, score - 0.15)
            label = "neutral"
        elif label == "neutral" and score < 0.6:
            label = "positive"
    elif neg_count > pos_count:
        if label == "positive":
            score = max(0.01, score - 0.15)
            label = "neutral"
        elif label == "neutral" and score < 0.6:
            label = "negative"

    return label, score

def analyze_text_sentiment(text):
    try:
        result = sentiment_pipeline(text[:512])[0]
        return adjust_sentiment_score(result, text)
    except:
        return "neutral", 0.0

def analyze_sentiment(articles):
    """Apply FinSentGPT to headlines (and snippets if available)."""
    # Always analyze headlines
    headline_results = articles['Headline'].apply(analyze_text_sentiment)
    articles['Headline Sentiment'] = headline_results.apply(lambda x: x[0])

    # Try using snippet if it exists, else copy from headline
    if 'Snippet' in articles.columns:
        snippet_results = articles['Snippet'].apply(analyze_text_sentiment)
        articles['Article Sentiment'] = snippet_results.apply(lambda x: x[0])
        articles['Sentiment Confidence'] = [
            max(h[1], s[1]) for h, s in zip(headline_results, snippet_results)
        ]
    else:
        articles['Article Sentiment'] = articles['Headline Sentiment']
        articles['Sentiment Confidence'] = headline_results.apply(lambda x: x[1])
        
        
    articles = articles[['Original_Date', 'Source', 'Headline', 'Link', 'Snippet',  'Headline Sentiment', 'Sentiment Confidence', 'Article Sentiment', 'Date', 'Updated_Date']]
    return articles

def process_articles(articles, existing_dates):
    """Process articles DataFrame to fix dates, remove duplicates, filter by keywords, and analyze sentiment."""
    articles = fix_dates(articles, existing_dates)
    articles = analyze_sentiment(articles)
    articles = extract_entities_from_df(articles)
    articles = articles[['Original_Date', 'Source', 'Headline', 'Link', 'Locations', 'Organizations', 'People', 'Topics', 'Events', 'Headline Sentiment', 'Sentiment Confidence', 'Article Sentiment', 'Date', 'Updated_Date']]
    articles.to_csv("real_time_news_FINAL.csv", index=False)
    return articles

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
            return today.strftime("%Y-%m-%d")

    match = re.search(days_ago_pattern, snippet)
    if match:
        days_ago = int(match.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    match = re.search(hours_ago_pattern, snippet)
    if match:
        return today.strftime("%Y-%m-%d")

    return today.strftime("%Y-%m-%d")


def extract_source(url):
    domain = urlparse(url).netloc
    return domain.replace("www.", "") if domain else "Unknown"


def fetch_real_time_news(API_KEY, SEARCH_ENGINE_ID, sources, keywords, API_REQUEST_LIMIT=100):
    
    data = []
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

                    data.append({
                        "Headline": headline,
                        "Link": link,
                        "Source": source,
                        "Snippet": snippet,
                        "Date": extracted_date if extracted_date else "Unknown"
                    })
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching results from {site}: {e}")
                continue
            
    return data

# entity extraction

import spacy
nlp = spacy.load("en_core_web_lg")

# FINAL LIST of predefined topic keywords
TOPIC_KEYWORDS = ["sanctions", "pipeline", "inflation", "OPEC", "trade war", "embargo", "energy crisis",
                  "oil production", "geopolitical tension", "oil demand", "export restrictions",
    "climate policy", "war", "oil spill", "energy transition", "supply chain",
    "price volatility", "fracking", "global economy", "petroleum reserves", "terrorism",
    "trade tariffs", "tensions", "crude", "oil prices", "oil supply", "disruption", "brent", 
    "petroleum", "fuel", "energy", "climate", "global warming"]

def extract_entities(headline):

    doc = nlp(headline)

    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    people = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    events = [ent.text for ent in doc.ents if ent.label_ == "EVENT"]

    topics = [word for word in TOPIC_KEYWORDS if word.lower() in headline.lower()]

    return {
        "Locations": locations,
        "Organizations": organizations,
        "People": people,
        "Topics": topics,
        "Events": events
    }

def extract_entities_from_df(articles):
    
    articles["Locations"] = articles["Headline"].apply(lambda x: extract_entities(x)["Locations"])
    articles["Organizations"] = articles["Headline"].apply(lambda x: extract_entities(x)["Organizations"])
    articles["People"] = articles["Headline"].apply(lambda x: extract_entities(x)["People"])
    articles["Topics"] = articles["Headline"].apply(lambda x: extract_entities(x)["Topics"])
    articles["Events"] = articles["Headline"].apply(lambda x: extract_entities(x)["Events"])
    
    articles = articles[['Original_Date', 'Source', 'Headline', 'Link', 'Snippet', 'Locations', 'Organizations', 'People', 'Topics', 'Events', 'Headline Sentiment', 'Sentiment Confidence', 'Article Sentiment', 'Date', 'Updated_Date']]
    return articles


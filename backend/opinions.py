import requests
from bs4 import BeautifulSoup
import csv
import time
import nltk
from nltk.tokenize import sent_tokenize
import spacy
import re
import os
from datetime import datetime, timedelta
import torch
from transformers import pipeline
from collections import Counter
from mongodb_utils import upload_to_mongodb

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

try:
    nlp = spacy.load("en_core_web_lg")
except Exception as e:
    print(f"Failed to load SpaCy model: {e}")
    exit(1)

try:
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
except Exception as e:
    print(f"Failed to load NER pipeline: {e}")
    exit(1)

base_url = "https://oilprice.com/Latest-Energy-News/World-News/Page-"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# keywords to extract relevant sentences from articles
geo_oil_keywords = {
    "tensions", "crude", "oil prices", "oil supply", "disruption", "brent",
    "sanctions", "embargo", "opec", "middle east", "russia", "ukraine", "petroleum",
    "fuel", "energy", "climate", "global warming", "conflict", "war", "economy", "inflation"
}

TOPIC_KEYWORDS = ["sanctions", "pipeline", "inflation", "OPEC", "trade war", "embargo", "energy crisis",
                      "oil production", "geopolitical tension", "oil demand", "export restrictions",
                      "climate policy", "war", "oil spill", "energy transition", "supply chain",
                      "price volatility", "fracking", "global economy", "petroleum reserves", "terrorism",
                      "trade tariffs", "tensions", "crude", "oil prices", "oil supply", "disruption", "brent",
                      "petroleum", "fuel", "energy", "climate", "global warming"
      ]

def score_sentence(sentence, keywords):
    # calculate relevance of a sentence based on keyword matches
    words = set(sentence.lower().split())
    return len(words.intersection(keywords))

def clean_text(text):
    # remove non-ascii characters and normalize whitespace
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def improved_summary(content, max_input_length=2000):
    # generate a summary from article content
    if content in ["Failed to fetch article", "Error fetching article"]:
        return "No information available"

    content = content[:max_input_length]
    sentences = sent_tokenize(content)
    scored_sentences = [(sent, score_sentence(sent, geo_oil_keywords)) for sent in sentences]
    relevant_sentences = [sent for sent, score in scored_sentences if score > 0]
    if not relevant_sentences:
        relevant_sentences = sentences[:5]
    full_info = " ".join(relevant_sentences)
    return clean_text(full_info)

def parse_date(date_str):
    # convert article date string with time to datetime object
    try:
        # expected format: "apr 03, 2025 at 18:58"
        return datetime.strptime(date_str, "%b %d, %Y at %H:%M")
    except ValueError as e:
        print(f"Failed to parse date '{date_str}': {e}")
        return None

def get_article_details(url):
    # fetch and parse article content and author from url
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return "Failed to fetch article", "Unknown Author"

        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("div", id="news-content", class_="wysiwyg clear")
        if not content_div:
            return "No main content found", "Unknown Author"

        article_content = []
        for p in content_div.find_all("p"):
            text = p.get_text(strip=True)
            if not (text.startswith("ADVERTISEMENT") or
                    "Oilprice.com" in text or
                    "More Top Reads" in text or
                    text.startswith("By ")):
                article_content.append(text)

        article_content = " ".join(article_content)

        author_tag = soup.find("p", class_="categoryArticle__meta")
        author = author_tag.text.strip().split("|")[-1].strip() if author_tag else "Unknown Author"

        return article_content, author
    except Exception as e:
        return f"Error fetching article: {str(e)}", "Unknown Author"

def scrape_headlines():
    # scrape articles from the last 24 hours
    current_time = datetime.now()  # current time
    cutoff_time = current_time - timedelta(hours=24)  # 24h ago
    print(f"Scraping articles from {cutoff_time} to {current_time}")

    headlines = []
    page = 1
    stop_scraping = False

    while not stop_scraping:
        url = f"{base_url}{page}.html"
        print(f"Trying URL: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch page {page}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.find_all("div", class_="categoryArticle"):
            title = article.find("h2", class_="categoryArticle__title").text.strip() if article.find("h2", class_="categoryArticle__title") else "No title"
            link = article.find("a")["href"] if article.find("a") else "No link"
            if link and link.startswith("/"):
                link = "https://oilprice.com" + link

            meta_tag = article.find("p", class_="categoryArticle__meta")
            if meta_tag:
                meta_text = meta_tag.text.strip()
                date, author = meta_text.split("|") if "|" in meta_text else (meta_text, "Unknown Author")
                date, author = date.strip(), author.strip()
            else:
                date, author = "Unknown Date", "Unknown Author"

            # parse article date with time
            article_date = parse_date(date)
            if article_date is None:
                print(f"Skipping article '{title}' due to unparseable date: {date}")
                continue

            # check if article is within last 24 hours
            if article_date < cutoff_time:
                print(f"Stopping at article '{title}' with date {article_date} (older than 24 hours)")
                stop_scraping = True
                break

            description = article.find("p", class_="categoryArticle__excerpt").text.strip() if article.find("p", class_="categoryArticle__excerpt") else "No description available"

            full_content, article_author = get_article_details(link)
            final_author = author if author != "Unknown Author" else article_author
            full_info = improved_summary(full_content)
            # entities = extract_entities(full_info, final_author)

            headlines.append({
                "Headline": title,
                "Link": link,
                "Date": date,
                "Description": description,
                "Author": final_author,
                "Full_info": full_info
            })

        if not stop_scraping:
            page += 1
            time.sleep(2)

    return headlines

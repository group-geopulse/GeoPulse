from transformers import pipeline
import pandas as pd

def get_next_available_date(date, existing_dates):
    """Find the next available date in existing_dates."""
    for existing_date in existing_dates:
        if existing_date >= date:
            return existing_date
    return date

def fix_dates(articles, existing_dates):
    """Fix dates in the articles DataFrame."""
    """Process articles DataFrame to fix dates and filter by keywords."""
    # Convert 'seendate' to 'OldDate' in the desired format
    articles['seendate'] = pd.to_datetime(articles['seendate']).dt.strftime('%Y-%m-%d')
    articles.rename(columns={'seendate': 'OldDate'}, inplace=True)

    # Update the dates in articles
    articles['Date'] = pd.to_datetime(articles['OldDate']).apply(lambda x: get_next_available_date(x, existing_dates))

    # Drop rows where Date is None (no next available date found)
    articles = articles.dropna(subset=['Date'])

    # Convert 'Date' to string format
    articles['Date'] = articles['Date'].dt.strftime('%Y-%m-%d')

    # Select the required columns and rename them
    articles = articles[['Date', 'OldDate', 'domain', 'title', 'url']]
    articles.rename(columns={'domain': 'Source', 'title': 'Headline', 'url': 'Link'}, inplace=True)
    return articles

def remove_duplicates(articles):
    """Remove duplicate headlines from the articles DataFrame."""
    duplicate_headlines = articles['Headline'].value_counts().loc[lambda x: x > 1]
    if len(duplicate_headlines) != 0:
        articles = articles[articles['Headline'].isin(duplicate_headlines.index)]
        print("Number of articles after dropping duplicates:", len(articles))
        return articles
    else:
        print("No duplicate headlines found.")
        return articles

def filter_by_keywords(articles):
    """Filter articles by keywords."""
    keywords = ['tensions', 'crude', 'oil prices', 'oil supply', 'disruption', 'brent', 'sanctions', 'embargo', 'opec', 'middle east', 'russia', 'ukraine', 'petroleum', 'fuel', 'energy', 'climate', 'global warming']
    for i in range(len(keywords)):
        keywords[i] = f'''( |[^a-z]|[^A-Z]){keywords[i]}( |[^a-z]|[^A-Z])'''
    relevant_articles = articles[articles['Headline'].str.contains('|'.join(keywords), case=False, regex=True)]
    if len(relevant_articles) == 0:
        print("No relevant articles found.")
        exit
    print(f"Number of relevant articles: {len(relevant_articles)}")
    print(f"Number of irrelevant articles: {len(articles) - len(relevant_articles)}")
    return relevant_articles

#Sentiment analysis functions
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
    articles['Headline_Sentiment'] = headline_results.apply(lambda x: x[0])

    # Try using snippet if it exists, else copy from headline
    if 'Snippet' in articles.columns:
        snippet_results = articles['Snippet'].apply(analyze_text_sentiment)
        articles['Article_Sentiment'] = snippet_results.apply(lambda x: x[0])
        articles['Sentiment_Confidence'] = [
            max(h[1], s[1]) for h, s in zip(headline_results, snippet_results)
        ]
    else:
        articles['Article_Sentiment'] = articles['Headline_Sentiment']
        articles['Sentiment_Confidence'] = headline_results.apply(lambda x: x[1])

    return articles

#def analyze_sentiment(articles):
    """Placeholder for sentiment analysis."""
    # Add sentiment analysis code here
    return articles

def process_articles(articles, existing_dates):
    """Process articles DataFrame to fix dates, remove duplicates, filter by keywords, and analyze sentiment."""
    articles = fix_dates(articles, existing_dates)
    articles = remove_duplicates(articles)
    articles = filter_by_keywords(articles)
    articles = analyze_sentiment(articles)
    articles = articles[['Date', 'OldDate', 'Source', 'Headline', 'Link', 'Headline_Sentiment', 'Article_Sentiment', 'Sentiment_Confidence']]
    return articles
    #articles = articles[['Date', 'OldDate', 'Source', 'Headline', 'Link']]
    #return articles
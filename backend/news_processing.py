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
    print(f"Number of relevant articles: {len(relevant_articles)}")
    print(f"Number of irrelevant articles: {len(articles) - len(relevant_articles)}")
    return relevant_articles

def analyze_sentiment(articles):
    """Placeholder for sentiment analysis."""
    # Add sentiment analysis code here
    return articles

def process_articles(articles, existing_dates):
    """Process articles DataFrame to fix dates, remove duplicates, filter by keywords, and analyze sentiment."""
    articles = fix_dates(articles, existing_dates)
    articles = remove_duplicates(articles)
    articles = filter_by_keywords(articles)
    articles = analyze_sentiment(articles)
    articles = articles[['Date', 'OldDate', 'Source', 'Headline', 'Link']]
    return articles
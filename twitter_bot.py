import feedparser
import tweepy
import random
import logging
from dotenv import load_dotenv
import os
import time
import re
from collections import Counter
import json
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Configuration file
import config

# Twitter API credentials from environment variables
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

# Validate environment variables
if not all([BEARER_TOKEN, API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    raise EnvironmentError("Missing Twitter API credentials in environment variables.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Tweepy client for Twitter API v2
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET_KEY,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# File to store posted articles to avoid duplicates
POSTED_ARTICLES_FILE = "posted_articles.json"

# Load posted articles from file
def load_posted_articles() -> List[str]:
    if os.path.exists(POSTED_ARTICLES_FILE):
        with open(POSTED_ARTICLES_FILE, "r") as file:
            return json.load(file)
    return []

# Save posted articles to file
def save_posted_articles(articles: List[str]) -> None:
    with open(POSTED_ARTICLES_FILE, "w") as file:
        json.dump(articles, file)

# Function to fetch and parse RSS feeds
def fetch_rss_feeds(feeds: List[str]) -> List[str]:
    articles = []
    for feed in feeds:
        logging.info(f'Fetching feed: {feed}')
        try:
            parsed_feed = feedparser.parse(feed)
            if parsed_feed.bozo:
                logging.warning(f'Failed to parse feed: {feed}')
                continue
            for entry in parsed_feed.entries:
                article = f"{entry.title} {entry.link}"
                articles.append(article)
                logging.info(f'Found article: {entry.title}')
        except Exception as e:
            logging.error(f'Error fetching feed {feed}: {e}')
    return articles

# Function to filter tweets based on inclusion and exclusion keywords
def filter_tweets(tweets: List[str]) -> List[str]:
    inclusion_keywords = ['technology', 'tech news', 'AI', 'artificial intelligence', 'latest gadgets']
    exclusion_keywords = ['war', 'child', 'children', 'teens', 'military']

    filtered_tweets = [
        tweet for tweet in tweets
        if any(keyword.lower() in tweet.lower() for keyword in inclusion_keywords) and
        not any(keyword.lower() in tweet.lower() for keyword in exclusion_keywords)
    ]
    return filtered_tweets

# Function to clean the tweet
def clean_tweet(tweet: str) -> str:
    cleaned_tweet = re.sub(r'[^\w\s]', '', tweet.lower())
    return cleaned_tweet

# Function to extract keywords from the cleaned tweet
def extract_keywords(cleaned_tweet: str) -> List[str]:
    keywords = cleaned_tweet.split()
    return keywords

# Function to create relevant hashtags for the tweet
def create_relevant_hashtags(tweet: str) -> List[str]:
    cleaned_tweet = clean_tweet(tweet)
    keywords = extract_keywords(cleaned_tweet)
    keyword_counts = Counter(keywords)
    most_common_keywords = [keyword for keyword, count in keyword_counts.most_common(5)]
    
    # Map keywords to generated hashtags
    hashtags = [config.GENERATED_HASHTAGS.get(keyword, '') for keyword in most_common_keywords if keyword in config.GENERATED_HASHTAGS]
    
    # Limit to 5 hashtags
    return hashtags[:5]

# Function to create a tweet
def create_tweet(articles: List[str], posted_articles: List[str]) -> Optional[str]:
    if not articles:
        logging.warning('No articles available to create a tweet.')
        return None

    # Filter out already posted articles
    new_articles = [article for article in articles if article not in posted_articles]
    
    if not new_articles:
        logging.info('No new articles to tweet.')
        return None

    # Randomly select an article to tweet
    selected_article = random.choice(new_articles)
    hashtags = create_relevant_hashtags(selected_article)
    
    tweet_content = f"{selected_article} {' '.join(hashtags)}"
    return tweet_content

# Function to post a tweet
def post_tweet(tweet: str) -> None:
    try:
        client.create_tweet(text=tweet)
        logging.info(f'Tweet posted: {tweet}')
    except Exception as e:
        logging.error(f'Error posting tweet: {e}')

# Main function to run the bot
def main():
    posted_articles = load_posted_articles()
    
    while True:
        articles = fetch_rss_feeds(config.RSS_FEEDS)
        tweet = create_tweet(articles, posted_articles)
        
        if tweet:
            post_tweet(tweet)
            posted_articles.append(tweet)  # Add the posted tweet to the list
            save_posted_articles(posted_articles)  # Save updated posted articles
        
        time.sleep(21600)  # Wait for six hours before fetching again

if __name__ == "__main__":
    main()
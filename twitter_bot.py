import feedparser
import tweepy
import random
import logging
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Twitter API credentials from environment variables
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_SECRET_KEY = os.getenv('API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')

# Check if all required credentials are loaded
if not all([BEARER_TOKEN, API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    raise EnvironmentError("Missing Twitter API credentials in environment variables.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Tweepy client for Twitter API v2
client = tweepy.Client(bearer_token=BEARER_TOKEN, 
                        consumer_key=API_KEY, 
                        consumer_secret=API_SECRET_KEY, 
                        access_token=ACCESS_TOKEN, 
                        access_token_secret=ACCESS_TOKEN_SECRET)

# RSS feed URLs for technology
rss_feeds = [
    'https://techcrunch.com/feed/',
    'https://www.theverge.com/rss/index.xml',
    'https://www.wired.com/feed/rss',
    'https://www.engadget.com/rss.xml',
    'https://www.cnet.com/rss/news/',
]

# Function to fetch and parse RSS feeds
def fetch_rss_feeds(feeds):
    articles = []
    for feed in feeds:
        logging.info(f'Fetching feed: {feed}')
        try:
            parsed_feed = feedparser.parse(feed)
            if parsed_feed.bozo:
                logging.warning(f'Failed to parse feed: {feed}')
                continue
            for entry in parsed_feed.entries:
                articles.append(entry.title + " " + entry.link)
                logging.info(f'Found article: {entry.title}')
        except Exception as e:
            logging.error(f'Error fetching feed {feed}: {e}')
    return articles

# Function to filter tweets based on inclusion and exclusion keywords
def filter_tweets(tweets):
    inclusion_keywords = ['technology', 'tech news', 'AI', 'artificial intelligence', 'latest gadgets']
    exclusion_keywords = ['war', 'child', 'children', 'teens', 'military']

    filtered_tweets = [
        tweet for tweet in tweets
        if any(keyword.lower() in tweet.lower() for keyword in inclusion_keywords) and
        not any(keyword.lower() in tweet.lower() for keyword in exclusion_keywords)
    ]

    return filtered_tweets

# Function to create a tweet
def create_tweet(articles):
    if not articles:
        logging.warning('No articles available to create a tweet.')
        return None

    filtered_articles = filter_tweets(articles)
    if not filtered_articles:
        logging.warning('No suitable articles found after filtering.')
        return None

    tweet_content = random.choice(filtered_articles)
    emojis = ["\ud83d\ude80", "\ud83d\udcbb", "\ud83d\udcf1", "\ud83d\uddde\ufe0f", "\ud83d\udd0d"]
    tweet_content += " " + random.choice(emojis)

    if len(tweet_content) > 280:
        tweet_content = tweet_content[:277] + "..."
        logging.info('Tweet content truncated to fit Twitter character limit.')

    logging.info(f'Created tweet: {tweet_content}')
    return tweet_content

# Function to post a tweet
def post_tweet(tweet, dry_run=True):
    if dry_run:
        logging.info(f'[DRY RUN] Tweet content: {tweet}')
        return

    try:
        client.create_tweet(text=tweet)
        logging.info("Tweet posted successfully!")
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")

# Main function to handle tweeting and scheduling
def main():
    logging.info('Starting the bot.')
    while True:
        # Post from RSS feeds
        articles = fetch_rss_feeds(rss_feeds)
        tweet = create_tweet(articles)
        if tweet:
            post_tweet(tweet, dry_run=False)  # Set dry_run=False to enable actual tweeting
        else:
            logging.warning('No tweet was created.')

        # Wait for 1 week before the next cycle
        logging.info("Sleeping for 1 hour...")
        time.sleep(3600)  # 1 Hour = 3,600 seconds

if __name__ == "__main__":
    main()

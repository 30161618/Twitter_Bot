import os
import openai
import tweepy
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import logging
import time
import feedparser  # For parsing RSS feeds

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Check for missing environment variables
if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, OPENAI_API_KEY]):
    logging.error("Missing one or more required environment variables. Please check your .env file.")
    exit(1)

# Set up Twitter API
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
)
twitter_api = tweepy.API(auth)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Scrape Technology News
def fetch_tech_news():
    logging.info("Fetching technology news from TechCrunch...")
    url = "https://techcrunch.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("h2.post-block__title > a")
        if articles:
            logging.info(f"Found {len(articles)} articles.")
            return [article.get_text(strip=True) for article in articles[:5]]
        else:
            logging.warning("No articles found on TechCrunch.")
            return []
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

# Fallback: Fetch Technology News from RSS Feed
def fetch_tech_news_from_rss():
    logging.info("Fetching technology news from RSS feed...")
    rss_url = "https://feeds.feedburner.com/TechCrunch/"
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            logging.info(f"Found {len(feed.entries)} articles in RSS feed.")
            return [entry.title for entry in feed.entries[:5]]
        else:
            logging.warning("No articles found in RSS feed.")
            return []
    except Exception as e:
        logging.error(f"Error fetching news from RSS feed: {e}")
        return []

# Generate Tweets with AI
def generate_tweet(topic):
    logging.info(f"Generating a tweet for topic: {topic}")
    prompt = f"Summarize this tech topic into a fun, engaging tweet with emojis and hashtags under 250 characters: {topic}"
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )
        tweet = response.choices[0].text.strip()
        logging.info(f"Generated tweet: {tweet}")
        return tweet
    except Exception as e:
        logging.error(f"Error generating tweet: {e}")
        return "🚀 Stay tuned for more tech updates! #TechNews #AI"

# Post a Tweet with retry mechanism
def post_tweet():
    logging.info("Starting the tweet posting process...")
    topics = fetch_tech_news()
    if not topics:  # Use RSS feed if scraping fails or returns no topics
        logging.warning("Scraping failed or returned no topics. Falling back to RSS feed.")
        topics = fetch_tech_news_from_rss()
    
    if not topics:  # If both fail, skip this cycle
        logging.error("No topics found even in RSS feed. Skipping this cycle.")
        return

    for topic in topics:
        tweet = generate_tweet(topic)
        retries = 3
        while retries > 0:
            try:
                twitter_api.update_status(tweet)
                logging.info(f"Successfully tweeted: {tweet}")
                break  # Exit retry loop if tweet is successful
            except tweepy.TweepError as e:
                if 'rate limit' in str(e).lower():
                    logging.warning("Rate limit reached. Retrying in 15 minutes...")
                    time.sleep(15 * 60)  # Wait for 15 minutes
                else:
                    logging.error(f"Error posting tweet: {e}")
                    break
            retries -= 1

# Scheduler for Automation
scheduler = BlockingScheduler()
scheduler.add_job(post_tweet, 'interval', hours=1)

if __name__ == "__main__":
    logging.info("Bot is starting...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot is shutting down...")

import os
import openai
import tweepy
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
import logging
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Check for missing environment variables
if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, OPENAI_API_KEY]):
    logging.error("Missing one or more required environment variables. Please check your .env file.")
    exit(1)
if not TWITTER_BEARER_TOKEN:
    logging.error("Missing Bearer Token. Please check your .env file.")
    exit(1)

# Set up Twitter API for posting tweets
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
)
twitter_api = tweepy.API(auth)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Fetch data from Twitter API using Bearer Token
def fetch_twitter_data(query):
    retries = 3
    backoff = 30  # Start with 30 seconds
    for attempt in range(retries):
        try:
            tweets = []
            logging.info(f"Fetching Twitter data for query: {query}")
            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
            url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=10"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'data' in data:
                tweets = [tweet['text'] for tweet in data['data']]
            logging.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
        except requests.exceptions.RequestException as e:
            if '429' in str(e):
                logging.warning(f"Rate limit reached. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
            else:
                logging.error(f"Error fetching Twitter data: {e}")
                break
    return []

# Fetch trending tweets using Bearer Token
def fetch_trending_tweets():
    keywords = ["technology", "AI", "artificial intelligence", "Books on Tech", "TechNews", "Tech News"]
    tweets = []
    selected_keywords = random.sample(keywords, k=2)  # Randomly pick 2 keywords per run
    for keyword in selected_keywords:
        time.sleep(5)  # Add delay between queries
        tweets.extend(fetch_twitter_data(keyword))
    return tweets

# Scrape Technology News
def fetch_tech_news():
    logging.info("Fetching technology news from TechCrunch...")
    url = "https://techcrunch.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("h2.post-block__title > a")
        logging.info(f"Found {len(articles)} articles.")
        return [article.get_text(strip=True) for article in articles[:5]]
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
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
        return "\ud83d\ude80 Stay tuned for more tech updates! #TechNews #AI"

# Post a Tweet with retry mechanism
def post_tweet():
    logging.info("Starting the tweet posting process...")
    trending_tweets = fetch_trending_tweets()

    if not trending_tweets:
        logging.warning("No trending tweets found. Falling back to tech news.")
        trending_tweets = fetch_tech_news()

    if not trending_tweets:
        logging.warning("No articles found. Generating an engaging tweet using OpenAI.")
        topic = "Exploring the latest in technology and innovation!"
        trending_tweets = [generate_tweet(topic)]

    for topic in trending_tweets:
        tweet = generate_tweet(topic)
        retries = 3
        while retries > 0:
            try:
                twitter_api.update_status(tweet)
                logging.info(f"Successfully tweeted: {tweet}")
                break  # Exit retry loop if tweet is successful
            except tweepy.errors.TweepyException as e:
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

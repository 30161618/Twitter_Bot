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
REQUIRED_ENV_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
    "OPENAI_API_KEY",
    "TWITTER_BEARER_TOKEN"
]

# Validate environment variables
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    exit(1)

# Assign variables
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up Twitter API for posting tweets
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
)
twitter_api = tweepy.API(auth)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Function to filter out unwanted topics
def filter_content(content):
    """
    Filters out topics containing unwanted keywords like 'war'.
    """
    excluded_keywords = ["war", "conflict", "battle", "military"]
    for keyword in excluded_keywords:
        if keyword.lower() in content.lower():
            logging.warning(f"Excluded content due to sensitive keyword '{keyword}': {content}")
            return False
    return True

def fetch_twitter_data(query, retries=3):
    """
    Fetch recent tweets based on a query using the Twitter API.
    """
    backoff = 30  # Initial backoff time in seconds
    for attempt in range(retries):
        try:
            logging.info(f"Fetching Twitter data for query: {query}")
            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
            url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=10"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            tweets = [
                tweet['text'] for tweet in data.get('data', [])
                if filter_content(tweet['text'])
            ]
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

def fetch_tech_news():
    """
    Scrape technology news headlines from TechCrunch.
    """
    logging.info("Fetching technology news from TechCrunch...")
    url = "https://techcrunch.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("h2.post-block__title > a")
        logging.info(f"Found {len(articles)} articles.")
        return [
            article.get_text(strip=True) for article in articles[:5]
            if filter_content(article.get_text(strip=True))
        ]
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []

def generate_tweet(topic):
    """
    Generate a tweet using OpenAI GPT based on a given topic.
    """
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

def post_tweet():
    """
    Post a tweet based on trending tweets or tech news. If unavailable, generate fallback content.
    """
    logging.info("Starting the tweet posting process...")
    keywords = ["technology", "AI", "artificial intelligence", "Books on Tech", "TechNews", "Tech News"]
    selected_keywords = random.sample(keywords, k=2)
    tweets = []

    for keyword in selected_keywords:
        time.sleep(5)  # Add delay between queries
        tweets.extend(fetch_twitter_data(keyword))

    if not tweets:
        logging.warning("No trending tweets found. Falling back to tech news.")
        tweets = fetch_tech_news()

    if not tweets:
        logging.warning("No tech news found. Using fallback topic for AI-generated tweet.")
        fallback_topic = "Exploring the latest in technology and innovation!"
        tweets = [generate_tweet(fallback_topic)]

    for topic in tweets:
        if not filter_content(topic):
            continue  # Skip any content flagged by the filter
        tweet = generate_tweet(topic)
        retries = 3
        while retries > 0:
            try:
                twitter_api.update_status(tweet)
                logging.info(f"Successfully tweeted: {tweet}")
                return  # Exit after successful tweet
            except tweepy.errors.TweepyException as e:
                if 'rate limit' in str(e).lower():
                    logging.warning("Rate limit reached. Retrying in 15 minutes...")
                    time.sleep(15 * 60)
                else:
                    logging.error(f"Error posting tweet: {e}")
                    break
            retries -= 1

# Scheduler for automation
scheduler = BlockingScheduler()
scheduler.add_job(post_tweet, 'interval', hours=1)

if __name__ == "__main__":
    logging.info("Bot is starting...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot is shutting down...")

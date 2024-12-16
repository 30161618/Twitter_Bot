import os
import tweepy
import requests
from bs4 import BeautifulSoup
import random
import schedule
import time
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# Fetch Twitter API keys from environment variables
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
    raise ValueError("Error: Missing Twitter API credentials. Please set the environment variables.")

# --- Initialize Twitter API ---
def twitter_api_setup():
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
    )
    return tweepy.API(auth)

twitter_api = twitter_api_setup()

# --- Helper Functions ---
# Scrape trending technology topics
def scrape_trending_tech():
    try:
        url = "https://techcrunch.com/"  # Replace with other tech news websites as needed
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract article titles from TechCrunch (update selector based on the website structure)
        articles = soup.select("h2.post-block__title > a")
        trends = [article.get_text(strip=True) for article in articles[:5]]  # Get top 5 articles
        return trends
    except Exception as e:
        print(f"Error scraping trends: {e}")
        return []

# Generate a Tweet with hashtags and emojis
def create_tweet(topic):
    emojis = ['🤖', '🚀', '💡', '📱', '✨', '🌐', '🔮', '📈']
    hashtags = ['#TechNews', '#AI', '#Innovation', '#FutureTech', '#Trending', '#TechTrends']
    
    tweet_template = [
        f"{random.choice(emojis)} {topic}. Stay updated with the latest tech trends! {random.choice(hashtags)}",
        f"{random.choice(emojis)} Breaking: {topic}. What are your thoughts? {random.choice(hashtags)}",
        f"Tech enthusiasts! {topic} is making waves. Don’t miss out. {random.choice(hashtags)}"
    ]
    return random.choice(tweet_template)[:250]  # Limit to 250 characters

# Post tweets automatically
def post_tech_tweets():
    topics = scrape_trending_tech()
    print(f"Fetched topics: {topics}")

    for topic in topics:
        tweet = create_tweet(topic)
        try:
            twitter_api.update_status(tweet)
            print(f"Tweeted: {tweet}")
        except Exception as e:
            print(f"Error posting tweet: {e}")

# --- Scheduler ---
# Run the bot every hour
schedule.every(1).hours.do(post_tech_tweets)

# Keep the script running
print("Bot is running...")
while True:
    schedule.run_pending()
    time.sleep(1)

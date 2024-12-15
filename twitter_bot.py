import os
import tweepy
import pyshorteners
import schedule
import time
import random
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

# --- Initialize APIs ---
# Twitter API setup
def twitter_api_setup():
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
    )
    return tweepy.API(auth)

twitter_api = twitter_api_setup()

# --- Helper Functions ---
# Fetch trending topics from Twitter
def fetch_trending_topics(location_woeid=1):  # WOEID 1 = Worldwide
    trends = twitter_api.get_place_trends(location_woeid)
    topics = [trend['name'] for trend in trends[0]['trends'] if trend['name'].startswith('#')]
    return topics[:5]  # Limit to top 5 trends

# Shorten URLs for tweets
def shorten_url(url):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(url)

# Create engaging tweet content
def create_tweet(trend):
    emoji = random.choice(['🔥', '📚', '✨', '💻', '🚀', '📱'])
    tweet_templates = [
        f"{emoji} {trend} is trending! Stay ahead with the latest updates. #ad",
        f"Trending now: {trend}! What are your thoughts? Let us know! 🚀",
        f"Don’t miss out on {trend}! It’s the talk of the town. #ad"
    ]
    return random.choice(tweet_templates)

# Post tweets automatically
def post_affiliate_tweets():
    trends = fetch_trending_topics()
    print(f"Fetched trends: {trends}")

    for trend in trends:
        tweet = create_tweet(trend)
        try:
            twitter_api.update_status(tweet)
            print(f"Tweeted: {tweet}")
        except Exception as e:
            print(f"Error posting tweet: {e}")

# --- Scheduler ---
# Run the bot every 2 hours
schedule.every(2).hours.do(post_affiliate_tweets)

# Keep the script running
print("Bot is running...")
while True:
    schedule.run_pending()
    time.sleep(1)

# --- Optimization Tips ---
# 1. **Relevance Filtering**: Filter trends for specific topics like technology, books, or gadgets.
# 2. **Rate-Limit Handling**: Respect Twitter's API rate limits. Add delays between API calls if necessary.
# 3. **Error Handling**: Use try-except blocks to handle network issues or invalid API responses.
# 4. **Tweet Variation**: Use random templates and emojis to keep tweets engaging and fresh.
# 5. **Compliance**: Always include hashtags like #ad to comply with affiliate marketing guidelines.
# 6. **Monitoring**: Log API responses and errors for debugging and performance monitoring.
# 7. **Scalability**: Consider deploying the bot to a server for 24/7 operation, such as Heroku or AWS.

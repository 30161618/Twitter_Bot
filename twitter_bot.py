import os
import openai
import tweepy
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up Twitter API
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
)
twitter_api = tweepy.API(auth)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Scrape Technology News
def fetch_tech_news():
    print("Fetching technology news from TechCrunch...")  # Debug log
    url = "https://techcrunch.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select("h2.post-block__title > a")
        print(f"Found {len(articles)} articles.")  # Debug log
        return [article.get_text(strip=True) for article in articles[:5]]
    except Exception as e:
        print(f"Error fetching news: {e}")  # Debug log
        return []

# Generate Tweets with AI
def generate_tweet(topic):
    print(f"Generating a tweet for topic: {topic}")  # Debug log
    prompt = f"Summarize this tech topic into a fun, engaging tweet with emojis and hashtags under 250 characters: {topic}"
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )
        tweet = response.choices[0].text.strip()
        print(f"Generated tweet: {tweet}")  # Debug log
        return tweet
    except Exception as e:
        print(f"Error generating tweet: {e}")  # Debug log
        return "🚀 Stay tuned for more tech updates! #TechNews #AI"

# Post a Tweet
def post_tweet():
    print("Starting the tweet posting process...")  # Debug log
    topics = fetch_tech_news()
    if not topics:
        print("No topics found. Skipping this cycle.")  # Debug log
        return
    
    for topic in topics:
        tweet = generate_tweet(topic)
        try:
            twitter_api.update_status(tweet)
            print(f"Successfully tweeted: {tweet}")  # Debug log
        except Exception as e:
            print(f"Error posting tweet: {e}")  # Debug log

# Scheduler for Automation
scheduler = BlockingScheduler()
scheduler.add_job(post_tweet, 'interval', hours=1)

print("Bot is running...")  # Debug log
scheduler.start()

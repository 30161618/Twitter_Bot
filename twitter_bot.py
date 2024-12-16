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
    url = "https://techcrunch.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select("h2.post-block__title > a")
    return [article.get_text(strip=True) for article in articles[:5]]

# Generate Tweets with AI
def generate_tweet(topic):
    prompt = f"Summarize this tech topic into a fun, engaging tweet with emojis and hashtags under 250 characters: {topic}"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
        temperature=0.7
    )
    return response.choices[0].text.strip()

# Post a Tweet
def post_tweet():
    topics = fetch_tech_news()
    for topic in topics:
        tweet = generate_tweet(topic)
        try:
            twitter_api.update_status(tweet)
            print(f"Tweeted: {tweet}")
        except Exception as e:
            print(f"Error posting tweet: {e}")

# Scheduler for Automation
scheduler = BlockingScheduler()
scheduler.add_job(post_tweet, 'interval', hours=1)

print("Bot is running...")
scheduler.start()

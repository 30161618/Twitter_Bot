import streamlit as st
import json
import os

# Load posted articles
def load_posted_articles():
    if os.path.exists("posted_articles.json"):
        with open("posted_articles.json", "r") as file:
            return json.load(file)
    return []

# Streamlit app
def main():
    st.title("Twitter Bot Dashboard")
    st.write("Monitor and manage your Twitter bot.")

    # Display posted articles
    st.header("Posted Articles")
    posted_articles = load_posted_articles()
    if posted_articles:
        for article in posted_articles:
            st.write(article)
    else:
        st.write("No articles posted yet.")

    # Add a button to manually trigger the bot
    if st.button("Run Bot Now"):
        st.write("Bot is running...")
        # Call your bot's main function here
        # Example: main_bot_function()
        st.write("Bot completed.")

if __name__ == "__main__":
    main()
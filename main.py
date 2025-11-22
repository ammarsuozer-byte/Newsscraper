import os
import requests
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime

# Download NLTK lexicon (required for sentiment analysis)
nltk.download('vader_lexicon', quiet=True)

class NewsReport:
    def __init__(self):
        self.api_key = os.environ.get("NEWS_API_KEY")
        self.sia = SentimentIntensityAnalyzer()
        
        # TARGET: High-impact global sources for Macro/Geopolitical risk
        self.target_domains = [
            "bloomberg.com", "reuters.com", "wsj.com", "ft.com", 
            "scmp.com", "aljazeera.com", "politico.com", "foxnews.com", "cnn.com"
        ]
        
    def fetch_news(self):
        domains = ",".join(self.target_domains)
        # Query: Focus on Catalysts (Policy, Trade, Conflict)
        keywords = '(tariff OR sanctions OR "trade war" OR "central bank" OR "interest rate" OR legislation OR election OR geopolitical OR "supply chain")'
        context = '(market OR economy OR trade)'
        noise = 'NOT (sport OR cricket OR movie OR review)'
        
        # Get up to 30 articles to filter for the best 20
        url = f"https://newsapi.org/v2/everything?q={keywords} AND {context} AND {noise}&domains={domains}&language=en&sortBy=publishedAt&pageSize=30&apiKey={self.api_key}"
        
        try:
            response = requests.get(url)
            # Check for API errors before returning articles
            if response.json().get("status") == "error":
                print(f"API Error: {response.json().get('message')}")
                return []
            return response.json().get('articles', [])
        except Exception as e:
            print(f"Connection Error: {e}")
            return []

    def analyze(self, text):
        # Returns the Compound Sentiment Score (-1.0 to 1.0)
        if not text: return 0.0
        return self.sia.polarity_scores(text)['compound']

    def save_report(self, articles):
        # Writes the content into a Markdown file for AI to read
        with open("report.md", "w", encoding="utf-8") as f:
            # Main Header
            f.write(f"# 🌍 Daily Geopolitical & Macro Risk Report\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')} | **Status:** Automated\n\n")
            f.write("> **INSTRUCTION FOR AI:** Analyze the articles below to identify top 3 short-term market risks (Negative Sentiment) and top 3 investment opportunities (Positive Sentiment).\n\n")
            f.write("---\n\n")
            
            count = 0
            for article in articles:
                if article['title'] == "[Removed]" or not article['description']: continue
                if count > 19: break # Limit to top 20
                
                # Data Extraction & Cleanup
                title = article.get('title', 'No Title')
                source = article['source']['name']
                link = article.get('url', '#')
                desc = article.get('description', '')
                content = article.get('content', '').split("[+")[0] # Removes the "\[+123 chars]" tag
                
                # Combine Description and Content to get the longest possible article summary
                full_text = f"{desc.strip()} {content.strip()}".replace("\n", " ")
                score = self.analyze(full_text)
                
                # Writing the Entry in Markdown for easy AI parsing
                f.write(f"## Article {count+1}: {title}\n")
                f.write(f"**Source:** {source} | **Sentiment Score:** `{score:.4f}`\n\n")
                f.write(f"{full_text}\n\n")
                f.write(f"[Read Original Article Here]({link})\n")
                f.write("---\n\n")
                count += 1
                
        print("Report saved to report.md")

if __name__ == "__main__":
    if os.environ.get("NEWS_API_KEY"):
        bot = NewsReport()
        articles = bot.fetch_news()
        print(f"Found {len(articles)} articles.")
        bot.save_report(articles)
    else:
        print("Error: NEWS_API_KEY environment variable not set.")

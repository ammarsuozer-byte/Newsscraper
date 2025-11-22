import os
import requests
import nltk
from fpdf import FPDF
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download NLTK lexicon for sentiment analysis
nltk.download('vader_lexicon', quiet=True)

class NewsReport:
    def __init__(self):
        self.api_key = os.environ.get("NEWS_API_KEY")
        self.sia = SentimentIntensityAnalyzer()
        
        # FIXED LIST: Covers Finance, diverse politics, and international regions
        self.finance_sources = [
            "bloomberg", "business-insider", "cnbc", "financial-times", 
            "the-wall-street-journal", "fortune", "reuters"
        ]
        self.diverse_sources = [
            "fox-news", # Right-leaning
            "cnn", # Left-leaning
            "bbc-news", # UK / International
            "al-jazeera-english", # Middle East / Global South
            "the-times-of-india" # Asia
        ]
        
    def fetch_news(self, query="stock market"):
        sources_str = ",".join(self.finance_sources + self.diverse_sources)
        url = f"https://newsapi.org/v2/everything?q={query}&sources={sources_str}&language=en&sortBy=publishedAt&apiKey={self.api_key}"
        
        response = requests.get(url)
        return response.json().get('articles', [])

    def analyze_sentiment(self, text):
        if not text: 
            return 0, "Neutral"
        score = self.sia.polarity_scores(text)['compound']
        
        if score >= 0.05:
            label = "Positive"
        elif score <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return score, label

    def generate_pdf(self, articles):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="Financial News & Sentiment Report", ln=1, align="C")
        pdf.ln(10)
        
        count = 0
        for article in articles:
            if count > 15: break # Limit to top 15 to keep PDF clean
            
            title = article.get('title', 'No Title')
            source = article['source']['name']
            desc = article.get('description', '')
            
            # Analyze Sentiment of the description
            score, label = self.analyze_sentiment(desc)
            
            # Formatting the Article Entry
            pdf.set_font("Arial", "B", 12)
            # Handle unicode issues roughly by encoding/decoding
            clean_title = title.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, f"{clean_title} ({source})")
            
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 5, txt=f"Sentiment: {label} (Score: {score})", ln=1)
            
            pdf.set_font("Arial", "I", 10)
            if desc:
                clean_desc = desc.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, clean_desc)
            
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            count += 1
            
        pdf.output("finance_report.pdf")
        print("PDF Generated successfully.")

if __name__ == "__main__":
    if not os.environ.get("NEWS_API_KEY"):
        print("Error: API Key not found.")
    else:
        bot = NewsReport()
        print("Fetching news...")
        articles = bot.fetch_news(query="finance OR stock OR economy")
        print(f"Found {len(articles)} articles. Analyzing...")
        bot.generate_pdf(articles)

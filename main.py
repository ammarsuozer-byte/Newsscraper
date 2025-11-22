import os
import requests
import nltk
from fpdf import FPDF
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download NLTK lexicon
nltk.download('vader_lexicon', quiet=True)

class NewsReport:
    def __init__(self):
        self.api_key = os.environ.get("NEWS_API_KEY")
        self.sia = SentimentIntensityAnalyzer()
        
        # DOMAINS LIST: Using specific website domains is more accurate than "source names"
        # This forces the API to look at these high-quality financial sites.
        self.target_domains = [
            "bloomberg.com",
            "reuters.com",
            "cnbc.com",
            "wsj.com",             # Wall Street Journal (US)
            "ft.com",              # Financial Times (UK/Global)
            "bbc.com",             # UK/Global Policy
            "aljazeera.com",       # Middle East (Oil/Energy news)
            "scmp.com",            # South China Morning Post (Asia/China Tech)
            "marketwatch.com"
        ]
        
    def fetch_news(self):
        # Join domains with commas
        domains_str = ",".join(self.target_domains)
        
        # QUERY: We search for strict financial terms and explicitly EXCLUDE noise
        # "AND NOT" removes common non-financial noise like movies, sports, and gossip
        query = '(stock OR "central bank" OR earnings OR "fed rate" OR "oil price" OR economy) AND NOT (movie OR cricket OR sport OR review OR "box office")'
        
        url = f"https://newsapi.org/v2/everything?q={query}&domains={domains_str}&language=en&sortBy=publishedAt&apiKey={self.api_key}"
        
        try:
            response = requests.get(url)
            data = response.json()
            if data.get("status") == "error":
                print(f"API Error: {data.get('message')}")
                return []
            return data.get('articles', [])
        except Exception as e:
            print(f"Connection Error: {e}")
            return []

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
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, txt="Global Market & Sentiment Report", ln=1, align="C")
        pdf.ln(5)
        
        count = 0
        for article in articles:
            # Skip articles that have been removed or have no content
            if article['title'] == "[Removed]" or not article['description']:
                continue
                
            if count > 19: break # Limit to top 20 relevant articles
            
            title = article.get('title', 'No Title')
            source = article['source']['name']
            desc = article.get('description', 'No description available.')
            link = article.get('url', '')
            
            # Analyze Sentiment
            score, label = self.analyze_sentiment(desc)
            
            # --- PDF ENTRY ---
            
            # 1. Title (Bold)
            pdf.set_font("Arial", "B", 12)
            clean_title = title.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"{clean_title} ({source})")
            
            # 2. Sentiment (Small, Grayish)
            pdf.set_font("Arial", size=9)
            pdf.set_text_color(100, 100, 100) # Gray
            pdf.cell(0, 5, txt=f"Sentiment: {label} ({score})", ln=1)
            pdf.set_text_color(0, 0, 0) # Reset to Black
            
            # 3. Description (Italic, wrapped text)
            pdf.set_font("Arial", "", 10)
            clean_desc = desc.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, clean_desc)
            
            # 4. Link (Blue, Clickable)
            pdf.set_font("Arial", "U", 9)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 5, txt="Read Full Article", link=link, ln=1)
            pdf.set_text_color(0, 0, 0) # Reset
            
            # Separator Line
            pdf.ln(3)
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
        print("Fetching focused financial news...")
        articles = bot.fetch_news()
        print(f"Found {len(articles)} articles. Analyzing...")
        bot.generate_pdf(articles)

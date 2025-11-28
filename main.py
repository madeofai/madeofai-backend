from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from collections import Counter
import praw
import json, os
import nltk
from nltk.corpus import stopwords
import inflect
import re

p = inflect.engine()

# Download stopwords if not already present
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

LOG_FILE = "search_log.json"
# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)

# ✅ CORS SHOULD BE ADDED ONLY ONCE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://madeofai.com",
        "https://www.madeofai.com",
        "https://madeofai.github.io",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "madeofai-backend"}

@app.get("/analyze")
async def analyze(term: str, request: Request):
    """Logs each search and returns Reddit word counts."""

    user_ip = request.client.host

    # Log search
    with open(LOG_FILE, "r+") as f:
        logs = json.load(f)
        logs.append({
            "term": term,
            "ip": user_ip,
            "timestamp": datetime.utcnow().isoformat()
        })
        f.seek(0)
        json.dump(logs, f, indent=2)

    try:
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="madeofai-bot"
        )

        results = []
        for submission in reddit.subreddit("all").search(term, limit=30):
            results.append(submission.title + " " + submission.selftext)



        text = " ".join(results)
        
        # Filter out words from the search term itself AND standard stopwords
        # Use regex to split by non-alphanumeric characters to handle punctuation
        search_terms_raw = set(re.split(r'[^a-zA-Z0-9]', term.lower()))
        # Remove empty strings
        search_terms_raw = {t for t in search_terms_raw if t}

        # Add singular and plural forms to search_terms
        expanded_terms = set()
        for t in search_terms_raw:
            expanded_terms.add(t)
            singular = p.singular_noun(t)
            if singular:
                expanded_terms.add(singular)
            plural = p.plural(t)
            if plural:
                expanded_terms.add(plural)
        
        search_terms = expanded_terms
        stop_words = set(stopwords.words('english'))
        
        # Split text by non-alphanumeric characters to clean words
        words = [
            w.lower() for w in re.split(r'[^a-zA-Z0-9]', text)
            if len(w) > 3 
            and w.lower() not in search_terms
            and w.lower() not in stop_words
        ]
        
        counts = Counter(words).most_common(60)

        return {"term": term, "status": "ok", "data": {"counts": counts}}

    except Exception as e:
        return {"term": term, "status": "error", "message": str(e)}

@app.get("/admin")
async def admin(key: str):

    """Return all logged searches as JSON."""
    ADMIN_KEY = os.getenv("ADMIN_KEY", "changeme")

    if key != ADMIN_KEY:
        return {"error": "Unauthorized"}

    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    return {"logs": logs}

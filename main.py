from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os, re
from collections import Counter
import praw
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing; restrict later to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load keys from .env
load_dotenv()

app = FastAPI(title="madeofai Reddit API")

# Allow frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Reddit client ---
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    check_for_async=False,
)
reddit.read_only = True

STOPWORDS = {
    "the","and","for","that","you","are","with","this","was","have","but",
    "not","your","from","just","they","about","what","when","who","why",
    "how","into","their","there","https","http","www","com","reddit","r","u"
}

def clean_tokens(text: str):
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 2 and t not in STOPWORDS]

@app.get("/")
def root():
    return {"status": "ok", "message": "madeofai backend is running"}

@app.get("/analyze")
async def analyze(term: str = Query(..., min_length=1)):
    term = term.strip()
    texts = []
    try:
        # Fetch 100 search results from all of Reddit
        for submission in reddit.subreddit("all").search(term, limit=100):
            if submission.title:
                texts.append(submission.title)
            if submission.selftext and submission.selftext not in ["[removed]", "[deleted]"]:
                texts.append(submission.selftext)
    except Exception as e:
        return {"term": term, "status": "error", "message": str(e)}

    joined = " ".join(texts)
    tokens = clean_tokens(joined)
    if not tokens:
        return {"term": term, "status": "no_data", "message": "No Reddit data found."}

    counts = Counter(tokens).most_common(80)
    return {"term": term, "status": "ok", "data": {"counts": counts}}

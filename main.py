from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import praw
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

app = FastAPI()

# ---- FIXED CORS POSITION ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing; later replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "madeofai backend is running"}

@app.get("/analyze")
def analyze(term: str):
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
        words = [w.lower() for w in text.split() if len(w) > 3]
        counts = Counter(words).most_common(60)
        return {"term": term, "status": "ok", "data": {"counts": counts}}
    except Exception as e:
        return {"term": term, "status": "error", "message": str(e)}


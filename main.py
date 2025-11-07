from fastapi import Request
from datetime import datetime
import json, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import praw
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

app = FastAPI()
LOG_FILE = "search_log.json"

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump([], f)

# ---- FIXED CORS POSITION ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing; later replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
origins = [
    "https://madeofai.com",
    "https://www.madeofai.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "madeofai backend is running"}

@app.get("/analyze")
async def analyze(term: str, request: Request):
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
        words = [w.lower() for w in text.split() if len(w) > 3]
        counts = Counter(words).most_common(60)
        return {"term": term, "status": "ok", "data": {"counts": counts}}
    except Exception as e:
        return {"term": term, "status": "error", "message": str(e)}
@app.get("/admin")
async def admin(key: str):
    ADMIN_KEY = os.getenv("ADMIN_KEY", "changeme")

    if key != ADMIN_KEY:
        return {"error": "Unauthorized"}

    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    return {"logs": logs}


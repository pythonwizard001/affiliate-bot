# scripts/syndicator_reddit.py
import os, glob, time
import praw, frontmatter

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER = os.getenv("REDDIT_USER")
REDDIT_PASS = os.getenv("REDDIT_PASS")
SUBREDDITS = os.getenv("REDDIT_SUBREDDITS","Entrepreneur,SideHustle").split(",")

def reddit_client():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USER,
        password=REDDIT_PASS,
        user_agent="affiliate-bot/0.1"
    )

def safe_post_to_subreddit(reddit, subreddit, title, selftext):
    sub = reddit.subreddit(subreddit.strip())
    # always submit as text post (value-first)
    return sub.submit(title=title, selftext=selftext)

def run():
    reddit = reddit_client()
    for md in sorted(glob.glob("content/posts/*.md"))[:3]:  # limit per run
        post = frontmatter.load(md)
        title = post.get('title')
        excerpt = (post.content[:800] + "\n\nRead more: " + os.getenv("SITE_URL","https://example.com"))
        for s in SUBREDDITS:
            try:
                print("Posting to", s.strip(), "->", title)
                safe_post_to_subreddit(reddit, s, title, excerpt)
                time.sleep(90)  # be polite
            except Exception as e:
                print("reddit post failed:", e)

if __name__ == "__main__":
    run()

# scripts/publisher_wordpress.py
import os, glob, requests
from pathlib import Path
import frontmatter

WP_SITE = os.getenv("WP_SITE")       # e.g. https://yourblog.wordpress.com
WP_USER = os.getenv("WP_USER")
WP_APP_PASS = os.getenv("WP_APP_PASS")  # application password

def publish_file(md_path):
    post = frontmatter.load(md_path)
    title = post.get('title')
    content = post.content
    api = WP_SITE.rstrip('/') + "/wp-json/wp/v2/posts"
    resp = requests.post(api, auth=(WP_USER, WP_APP_PASS), json={
        "title": title,
        "content": content,
        "status": "publish"
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()

def publish_all():
    for md in glob.glob("content/posts/*.md"):
        try:
            r = publish_file(md)
            print("Published:", md, r.get("link"))
        except Exception as e:
            print("Failed publish:", md, e)

if __name__ == "__main__":
    publish_all()

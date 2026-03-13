# scripts/syndicator_mastodon.py
import os, glob, time, requests, frontmatter, json
CFG = json.load(open("config.json","r",encoding="utf8"))

BASE = os.getenv("MASTODON_BASE_URL", CFG.get("mastodon_base_url","")).rstrip("/")
TOKEN = os.getenv("MASTODON_TOKEN")
SITE_URL = os.getenv("SITE_URL", CFG.get("site_url"))

def post_status(status):
    url = f"{BASE}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.post(url, headers=headers, data={"status": status})
    resp.raise_for_status()
    return resp.json()

def build_status_from_md(md_path):
    post = frontmatter.load(md_path)
    title = post.get("title")
    excerpt = post.content[:400].strip()
    slug = md_path.split("/")[-1].replace(".md","")
    link = SITE_URL.rstrip("/") + "/" + slug
    status = f"{title}\n\n{excerpt}\n\nRead: {link}\n\n#{CFG['brand'].replace(' ','')}"
    return status

if __name__ == "__main__":
    files = sorted(glob.glob("content/posts/*.md"), key=lambda p: p, reverse=True)[:3]
    for md in files:
        try:
            status = build_status_from_md(md)
            res = post_status(status)
            print("Mastodon posted id:", res.get("id"))
            time.sleep(6)
        except Exception as e:
            print("Mastodon error:", e)

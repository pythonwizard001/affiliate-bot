# scripts/syndicator_telegram.py
import os, glob, time, requests
import frontmatter, json
CFG = json.load(open("config.json","r",encoding="utf8"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SITE_URL = os.getenv("SITE_URL", CFG.get("site_url"))

def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode":"Markdown"}
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def build_message_from_md(md_path):
    post = frontmatter.load(md_path)
    title = post.get("title")
    excerpt = (post.content[:700] + "...")
    slug = md_path.split("/")[-1].replace(".md","")
    link = SITE_URL.rstrip("/") + "/" + slug
    msg = f"*{title}*\n\n{excerpt}\n\nRead the full article on {CFG['brand']}: {link}"
    return msg

if __name__ == "__main__":
    files = sorted(glob.glob("content/posts/*.md"), key=lambda p: p, reverse=True)[:3]
    for md in files:
        try:
            msg = build_message_from_md(md)
            resp = post_to_telegram(msg)
            print("Telegram posted:", md, resp.get("ok"))
            time.sleep(6)
        except Exception as e:
            print("Telegram error:", e)

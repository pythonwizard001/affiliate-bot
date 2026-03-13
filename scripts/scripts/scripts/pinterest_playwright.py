# scripts/pinterest_playwright.py
import os, time, glob, json
from playwright.sync_api import sync_playwright
import frontmatter

CFG = json.load(open("config.json","r",encoding="utf8"))
EMAIL = os.getenv("PINTEREST_EMAIL")
PASSWORD = os.getenv("PINTEREST_PASSWORD")
BOARD = os.getenv("PINTEREST_BOARD")
SITE_URL = os.getenv("SITE_URL", CFG.get("site_url"))

def pin_article(md_path):
    post = frontmatter.load(md_path)
    title = post.get("title")
    excerpt = (post.content[:400] + "...")
    slug = md_path.split("/")[-1].replace(".md","")
    link = SITE_URL.rstrip("/") + "/" + slug
    # Try to find an image for the post
    imgs = sorted(glob.glob("content/posts/images/*"), key=lambda p: p, reverse=True)
    image = imgs[0] if imgs else None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.pinterest.com/login/")
        time.sleep(2)
        # login
        try:
            page.fill("input[name='id']", EMAIL)
            page.fill("input[name='password']", PASSWORD)
            page.click("button[type='submit']")
        except Exception:
            # alternate selectors
            page.fill("input#email", EMAIL)
            page.fill("input#password", PASSWORD)
            page.click("button[type='submit']")
        time.sleep(5)
        # open create pin page
        page.goto("https://www.pinterest.com/pin-builder/")
        time.sleep(3)
        if image:
            page.set_input_files("input[type='file']", image)
            time.sleep(2)
        # description
        try:
            page.fill("textarea[name='description']", f"{title}\n\n{excerpt}\n\n{link}")
        except Exception:
            # fallback: attempt to type
            page.keyboard.type(f"{title}\n\n{excerpt}\n\n{link}")
        # choose board (open board dropdown)
        try:
            page.click("div[data-test-id='board-dropdown']")
            time.sleep(1)
            page.fill("input[placeholder='Search boards']", BOARD)
            time.sleep(1)
            page.click(f"text={BOARD}")
        except Exception:
            pass
        # publish/save
        try:
            page.click("button:has-text('Publish')")
        except Exception:
            try:
                page.click("button:has-text('Save')")
            except Exception as e:
                print("Could not click publish/save:", e)
        time.sleep(3)
        browser.close()
    return True

if __name__ == "__main__":
    files = sorted(glob.glob("content/posts/*.md"), key=lambda p: p, reverse=True)[:2]
    for f in files:
        try:
            print("Pinning", f)
            pin_article(f)
            time.sleep(6)
        except Exception as e:
            print("Pin failed:", e)

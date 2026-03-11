# scripts/medium_publish_playwright.py
import os, time
from playwright.sync_api import sync_playwright
import frontmatter

MEDIUM_EMAIL = os.getenv("MEDIUM_EMAIL")
MEDIUM_PASSWORD = os.getenv("MEDIUM_PASSWORD")  # store in GitHub Secrets

def publish(md_path):
    post = frontmatter.load(md_path)
    title = post.get('title')
    content = post.content
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://medium.com/m/signin")
        # Medium's login UI changes; this script may require minor edits per UI update.
        page.fill("input[type='email']", MEDIUM_EMAIL)
        page.click("button:has-text('Continue')")  # UI text may differ
        time.sleep(2)
        page.fill("input[type='password']", MEDIUM_PASSWORD)
        page.click("button:has-text('Sign in')")
        time.sleep(3)
        page.goto("https://medium.com/new-story")
        time.sleep(3)
        page.fill("h1", title)
        page.fill("article", content[:15000])  # paste portion; UI paste may need more fancy script
        time.sleep(2)
        # Click publish - selectors may need update
        page.click("button:has-text('Publish')")
        time.sleep(2)
        browser.close()
        return True

if __name__ == "__main__":
    # Example usage: publish the top 1 file (manual call)
    import glob
    for md in glob.glob("content/posts/*.md")[:1]:
        print("Publishing to Medium (via Playwright):", md)
        publish(md)

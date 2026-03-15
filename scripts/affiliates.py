# scripts/affiliates.py
import csv
import os
import difflib
import requests
from urllib.parse import urlparse, urljoin, urlencode
from pathlib import Path
import frontmatter
import json
from datetime import datetime

# CONFIG
CFG = json.load(open("config.json","r",encoding="utf8"))
SITE_URL = os.getenv("SITE_URL", CFG.get("site_url", "https://your-site.example"))
AFFILIATES_CSV = "affiliates.csv"
REDIRECT_DIR = Path("content/go")   # static redirect pages will be placed here
REDIRECT_DIR.mkdir(parents=True, exist_ok=True)

# Load affiliate catalog
def load_affiliates(csv_path=AFFILIATES_CSV):
    items = []
    if not os.path.exists(csv_path):
        return items
    with open(csv_path, newline='', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            items.append({
                "product_name": r.get("product_name","").strip(),
                "retailer": r.get("retailer","").strip(),
                "affiliate_url": r.get("affiliate_url","").strip(),
                "notes": r.get("notes","").strip()
            })
    return items

# Find best match using difflib; returns affiliate dict or None
def find_best_affiliate(product_title, threshold=0.55):
    items = load_affiliates()
    if not items:
        return None
    names = [i["product_name"] for i in items]
    # difflib returns close matches; measure ratio separately
    matches = difflib.get_close_matches(product_title, names, n=5, cutoff=0.1)
    best = None
    best_ratio = 0.0
    for name in matches:
        ratio = difflib.SequenceMatcher(None, product_title.lower(), name.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = next((i for i in items if i["product_name"]==name), None)
    # simple fallback: also check if product_title contains product_name substring
    if not best:
        for i in items:
            if i["product_name"].lower() in product_title.lower():
                best = i
                best_ratio = 0.6
                break
    if best and best_ratio >= threshold:
        best_copy = best.copy()
        best_copy["_match_score"] = best_ratio
        return best_copy
    return None

# Validate that affiliate_url likely matches product by checking page title similarity
def validate_affiliate_link(affiliate_url, product_title, max_ratio_fail=0.35, timeout=8):
    # follow redirects, fetch page title
    try:
        r = requests.get(affiliate_url, timeout=timeout, allow_redirects=True, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code >= 400:
            return False, "http_error"
        # try to extract <title>
        text = r.text
        start = text.find("<title")
        if start != -1:
            # naive extract; not a full parser but works often
            start = text.find(">", start) + 1
            end = text.find("</title>", start)
            title = text[start:end].strip() if end!=-1 else ""
        else:
            title = ""
        if not title:
            # no title found; accept but mark as unvalidated
            return True, "no_title"
        ratio = difflib.SequenceMatcher(None, product_title.lower(), title.lower()).ratio()
        return (ratio >= max_ratio_fail), f"title_ratio:{ratio:.2f}"
    except Exception as e:
        return False, f"exception:{str(e)[:80]}"

# Create redirect HTML page which includes GA (if you include GA script in your site template this still registers)
REDIRECT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0.9; url={target}">
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Redirecting…</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;text-align:center;padding:60px;color:#333}} .btn{{display:inline-block;padding:12px 18px;background:#0b74de;color:#fff;border-radius:6px;text-decoration:none}}</style>
</head>
<body>
<h1>Redirecting to {retailer}</h1>
<p>If you are not redirected automatically, <a class="btn" href="{target}">click here to proceed</a>.</p>
<!-- Optional: small noscript redirect -->
<noscript><meta http-equiv="refresh" content="0; url={target}"></noscript>
</body>
</html>
"""

def make_safe_slug(text):
    # simple slug for file names
    s = "".join([c if c.isalnum() or c in "-_" else "-" for c in text.lower()])[:80]
    s = "-".join([part for part in s.split("-") if part])
    return s[:80]

# Create redirect page and return redirect URL on your site
def create_redirect_page(product_title, affiliate_url, retailer_label=None):
    slug = make_safe_slug(product_title)
    filename = REDIRECT_DIR / (slug + ".html")
    retailer_label = retailer_label or urlparse(affiliate_url).netloc
    html = REDIRECT_TEMPLATE.format(target=affiliate_url, retailer=retailer_label)
    filename.write_text(html, encoding="utf8")
    # Return the public URL
    redirect_path = "/".join([SITE_URL.rstrip("/"), "go", filename.name])
    return redirect_path, str(filename)

# Insert affiliate link into markdown content - replace placeholder token
def insert_affiliate_link_in_markdown(md_path, redirect_url, anchor_text="Buy on Retailer"):
    post = frontmatter.load(md_path)
    body = post.content
    # look for placeholder token [AFFILIATE_LINK] or custom token
    if "[AFFILIATE_LINK]" in body:
        body = body.replace("[AFFILIATE_LINK]", f"[{anchor_text}]({redirect_url})")
    else:
        # fallback: append CTA at bottom
        body = body + f"\n\n**{anchor_text}:** [{redirect_url}]({redirect_url})\n"
    post.content = body
    Path(md_path).write_text(frontmatter.dumps(post), encoding="utf8")
    return md_path

# High-level: for a single article, find affiliate, validate, create redirect, insert link
def process_article(md_path):
    post = frontmatter.load(md_path)
    title = post.get("title") or Path(md_path).stem
    print("Processing affiliate for:", title)
    candidate = find_best_affiliate(title)
    if not candidate:
        print("No affiliate match found for", title)
        return {"status":"no_match", "title":title}
    # validate
    ok, reason = validate_affiliate_link(candidate["affiliate_url"], title)
    if not ok:
        print("Validation failed:", reason, "for", candidate["affiliate_url"])
        # still allow but mark as review-needed
        redirect, file_path = create_redirect_page(title, candidate["affiliate_url"], candidate.get("retailer"))
        insert_affiliate_link_in_markdown(md_path, redirect, anchor_text=f"Buy on {candidate.get('retailer','Retailer')}")
        return {"status":"created_unvalidated", "title":title, "redirect":redirect, "reason":reason}
    # OK validated
    redirect, file_path = create_redirect_page(title, candidate["affiliate_url"], candidate.get("retailer"))
    insert_affiliate_link_in_markdown(md_path, redirect, anchor_text=f"Buy on {candidate.get('retailer','Retailer')}")
    print("Inserted redirect:", redirect)
    return {"status":"ok", "title":title, "redirect":redirect, "affiliate":candidate}

if __name__ == "__main__":
    # quick test: process all drafted posts
    for p in Path("content/posts").glob("*.md"):
        res = process_article(str(p))
        print(res)

def append_utm(url, source="hometechhive", medium="affiliate", campaign=None):
    try:
        parsed = urlparse(url)
        q = dict()
        if parsed.query:
            for part in parsed.query.split("&"):
                k,v = part.split("=",1) if "=" in part else (part, "")
                q[k] = v
        q.update({
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign or datetime.utcnow().strftime("auto-%Y%m%d")
        })
        newq = urlencode(q)
        rebuilt = parsed._replace(query=newq).geturl()
        return rebuilt
    except Exception:
        return url

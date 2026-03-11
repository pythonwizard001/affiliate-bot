# scripts/gen_article.py
import os, frontmatter, datetime
from pathlib import Path
from scripts.queue_manager import fetch_pending, mark
from scripts.gen_outline import gen_outline
from scripts.utils import hf_generate

MAX_BATCH = int(os.getenv("BATCH_SIZE", "6"))
OUT_DIR = Path("content/posts")

def generate_section(title, section_heading):
    prompt = f"Write 2 short paragraphs for the section '{section_heading}' in an article titled: '{title}'. Keep it factual and include a short concluding sentence."
    return hf_generate(prompt, model="distilgpt2", max_length=240)

def create_markdown_file(brief, outline_obj, body_html):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    post = frontmatter.Post(body_html)
    post['title'] = brief['title']
    post['date'] = now
    post['tags'] = [brief['seed'], 'affiliate', 'review']
    filepath = OUT_DIR / f"{brief['slug']}.md"
    filepath.write_text(frontmatter.dumps(post), encoding="utf8")
    return filepath.as_posix()

def generate_for_brief(brief):
    outline = gen_outline(brief['title'])
    sections = outline.get("outline", ["Introduction","Top picks","Conclusion"])
    content = f"# {brief['title']}\n\n**{outline.get('meta','')}**\n\n"
    for sec in sections:
        text = generate_section(brief['title'], sec)
        content += f"## {sec}\n\n{text}\n\n"
    # faq
    content += "## FAQ\n\n"
    for q in outline.get("faq", []):
        content += f"**Q: {q.get('q','')}**\n\n{q.get('a','')}\n\n"
    # affiliate disclosure placeholder
    content += "\n**Affiliate disclosure:** This post may contain affiliate links. I may earn a small commission at no extra cost to you.\n"
    return create_markdown_file(brief, outline, content)

def run_batch():
    pending = fetch_pending(limit=MAX_BATCH)
    if not pending:
        print("No pending briefs.")
        return
    for b in pending:
        mark(b['id'], 'processing')
    for b in pending:
        try:
            fname = generate_for_brief(b)
            print("Generated:", fname)
            mark(b['id'], 'drafted')
        except Exception as e:
            print("Failed for", b['id'], e)
            mark(b['id'], 'pending')  # retry later

if __name__ == "__main__":
    run_batch()

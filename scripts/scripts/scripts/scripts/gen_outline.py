# scripts/gen_outline.py
import json
from scripts.utils import hf_generate

PROMPT = """Produce a concise SEO JSON outline for the article titled: "{title}".
Return valid JSON exactly with fields:
{{"meta": "...", "outline": ["h2 heading","h2 heading", ...], "faq":[{{"q":"...","a":"..."}}]}}"""

def gen_outline(title):
    prompt = PROMPT.format(title=title)
    raw = hf_generate(prompt, model="distilgpt2", max_length=200)
    # try to extract JSON substring
    try:
        start = raw.find("{")
        raw_json = raw[start:]
        return json.loads(raw_json)
    except Exception:
        # fallback
        return {"meta": title, "outline": ["Introduction","Top picks","How to choose","Conclusion"], "faq":[{"q":"Is it worth it?","a":"Depends on needs."}]}

# scripts/discover.py
from pytrends.request import TrendReq
import requests, time, hashlib
from scripts.queue_manager import init_db, enqueue_briefs

def suggestions(q):
    try:
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client":"firefox","q": q}
        r = requests.get(url, params=params, timeout=6)
        if r.status_code == 200:
            return r.json()[1][:8]
    except Exception:
        pass
    return []

def get_trending_seeds(max_items=80):
    py = TrendReq(hl='en-US', tz=360)
    seeds = set()
    try:
        trends = py.trending_searches(pn='united_states').head(50).tolist()
        for t in trends:
            seeds.add(t)
    except Exception:
        pass
    # add some generic categories if empty
    if not seeds:
        seeds.update(["portable blender","wireless earbuds","home projector","backpack"])
    # expand with suggestions
    seeds_list = list(seeds)[:max_items]
    expanded = set(seeds_list)
    for s in seeds_list:
        for sug in suggestions(s):
            expanded.add(sug)
        time.sleep(0.15)
    return list(expanded)[:max_items]

def make_briefs_from_seeds(seeds, per_seed=4):
    tpls = [
        "Best {} for beginners: top picks and buying guide",
        "{} review: features, pros & cons",
        "Top 10 {} in 2026 — comparison & buyer's guide",
        "How to choose the right {} for you",
        "{} vs alternatives: which one to buy"
    ]
    briefs=[]
    for s in seeds:
        for t in tpls[:per_seed]:
            title = t.format(s)
            slug = hashlib.sha1(title.encode()).hexdigest()[:12] + "-" + "-".join(title.lower().split())[:50]
            briefs.append({"seed": s, "title": title, "slug": slug, "meta": title[:150]})
    return briefs

if __name__ == "__main__":
    init_db()
    seeds = get_trending_seeds(max_items=80)
    briefs = make_briefs_from_seeds(seeds, per_seed=4)  # ~320 briefs
    enqueue_briefs(briefs)
    print("Enqueued briefs:", len(briefs))

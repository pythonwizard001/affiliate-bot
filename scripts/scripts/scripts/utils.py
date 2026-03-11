# scripts/utils.py
import os, json, time, hashlib, requests
from pathlib import Path

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
CACHE = Path("data/hf_cache.json")

def _load_cache():
    try:
        if CACHE.exists():
            return json.loads(CACHE.read_text(encoding="utf8"))
    except Exception:
        pass
    return {}

def _save_cache(d):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(d), encoding="utf8")

def hf_generate(prompt, model="distilgpt2", max_length=300):
    key = hashlib.sha1((model + prompt).encode()).hexdigest()
    cache = _load_cache()
    if key in cache:
        return cache[key]

    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_length, "do_sample": True, "top_k":50}}
    for attempt in range(6):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 503:
                time.sleep(2**attempt)
                continue
            r.raise_for_status()
            data = r.json()
            # model response shape varies; handle both
            out = ""
            if isinstance(data, list) and data and "generated_text" in data[0]:
                out = data[0]["generated_text"]
            else:
                out = json.dumps(data)
            cache[key] = out
            _save_cache(cache)
            return out
        except Exception:
            time.sleep(2**attempt)
    raise RuntimeError("hf_generate: failed after retries")

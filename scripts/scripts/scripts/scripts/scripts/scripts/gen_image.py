# scripts/gen_image.py
import os, requests, time, base64
from pathlib import Path

HORD_API = os.getenv("HORD_API_KEY")

def request_image(prompt, filename=None):
    url = "https://stablehorde.net/api/v2/generate/async"
    headers = {"apikey": HORD_API} if HORD_API else {}
    payload = {"prompt": prompt, "params":{"width":512,"height":512,"steps":20}}
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    job = r.json().get("id")
    check = f"https://stablehorde.net/api/v2/generate/check/{job}"
    for _ in range(40):
        s = requests.get(check, timeout=10)
        if s.status_code == 200:
            st = s.json()
            if st.get("done"):
                gens = st.get("generations", [])
                if gens:
                    b64 = gens[0].get("img")  # base64
                    img = base64.b64decode(b64)
                    outdir = Path("content/posts/images")
                    outdir.mkdir(parents=True, exist_ok=True)
                    if not filename:
                        filename = outdir / f"{job}.png"
                    else:
                        filename = outdir / filename
                    with open(filename, "wb") as f:
                        f.write(img)
                    return str(filename)
        time.sleep(2)
    return None

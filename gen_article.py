- name: Attach affiliate links (map -> redirect -> inject)
  run: |
    python -c "from scripts.affiliates import process_article; import glob; import json
    files = sorted(glob.glob('content/posts/*.md'))
    results=[]
    for f in files:
      results.append(process_article(f))
    print(json.dumps(results, indent=2))"

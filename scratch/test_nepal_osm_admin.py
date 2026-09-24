import urllib.request
import json

q = """[out:json][timeout:25];
(
  relation["boundary"="administrative"]["admin_level"~"6|7|8"](28.02,85.12,28.38,85.58);
);
out tags;
"""

mirrors = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for m in mirrors:
    try:
        print(f"Trying {m}...")
        req = urllib.request.Request(m, data=q.encode('utf-8'), headers={'User-Agent': 'SatQuery-AI/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elems = data.get("elements", [])
            print(f"Success! {len(elems)} admin relations found.")
            for el in elems:
                tags = el.get("tags", {})
                print(f"ID: {el['id']} | Level: {tags.get('admin_level')} | Name: {tags.get('name:en') or tags.get('name')}")
            break
    except Exception as e:
        print(f"Failed {m}: {e}")

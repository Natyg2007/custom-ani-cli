#!/usr/bin/env python3

import json
import os
import re
import requests

HISTORY_FILE = os.path.expanduser("~/.local/state/ani-cli/ani-hsts")
CACHE_FILE = os.path.expanduser("~/custom-ani-cli/hash-to-anilist.json")
ANILIST_TOKEN = os.getenv("ANILIST_TOKEN")

def normalize(text):
    return re.sub(r'\W+', '', text or '').lower()

def load_history():
    history = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue
            ep_no, _id, title = parts
            match = re.search(r"(.*?) \((\d+) episodes\)", title)
            if match:
                raw_title, total_eps = match.groups()
                total_eps = int(total_eps)
            else:
                raw_title = title.strip()
                total_eps = None
            history.append({
                "watched": int(ep_no),
                "id": _id,
                "raw_title": raw_title,
                "total_eps": total_eps
            })
    return history

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def fetch_anilist(title):
    url = "https://graphql.anilist.co"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ANILIST_TOKEN}"
    }
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        id
        title {
          romaji
          english
        }
        episodes
        status
      }
    }
    '''
    response = requests.post(url, headers=headers, json={
        "query": query,
        "variables": {"search": title}
    })
    if response.status_code == 200:
        return response.json().get("data", {}).get("Media", {})
    return {}

def match_title(raw_title, entry):
    raw_norm = normalize(raw_title)
    return any(raw_norm == normalize(name) for name in (
        entry.get("romaji", ""),
        entry.get("english", ""),
        entry.get("title", ""),
        *entry.get("aliases", [])
    ))

def main():
    history = load_history()
    cache = load_cache()
    updated = False

    for entry in history:
        cached = next((c for c in cache if c["hash"] == entry["id"] or match_title(entry["raw_title"], c)), None)

        if not cached:
            ani = fetch_anilist(entry["raw_title"])
            if not ani:
                print(f"{entry['id']}\t{entry['raw_title']} - episode {entry['watched']}/{entry['total_eps'] or '?'}")
                continue
            cached = {
                "title": entry["raw_title"],
                "romaji": ani["title"].get("romaji", ""),
                "english": ani["title"].get("english", ""),
                "anilist_id": ani.get("id"),
                "episodes": ani.get("episodes"),
                "status": ani.get("status"),
                "hash": entry["id"],
                "aliases": []
            }
            cache.append(cached)
            updated = True

        romaji = cached.get("romaji", "")
        english = cached.get("english", "")
        ep_total = cached.get("episodes") or entry.get("total_eps") or "?"

        if english and english != romaji:
            display_title = f"{english} ({romaji})"
        else:
            display_title = romaji or entry["raw_title"]

        print(f"{entry['id']}\t{display_title} - episode {entry['watched']}/{ep_total}")

    if updated:
        save_cache(cache)

if __name__ == "__main__":
    main()

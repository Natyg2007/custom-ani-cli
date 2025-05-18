#!/usr/bin/env python3

import json
import os
import re
import requests

HISTORY_FILE = os.path.expanduser("~/.local/state/ani-cli/ani-hsts")
CACHE_FILE = os.path.expanduser("~/.cache/ani-cli-anilist-ids.json")
ANILIST_TOKEN = os.getenv("ANILIST_TOKEN")

def load_history():
    history = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                ep_no, _id, title = parts
                match = re.match(r"(.+?) \((\d+) episodes\)", title)
                if match:
                    raw_title, total_eps = match.groups()
                    history.append({
                        "watched": int(ep_no),
                        "id": _id,
                        "raw_title": raw_title.strip(),
                        "total_eps": int(total_eps)
                    })
    return history

def fetch_anilist_data(title):
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
    response = requests.post(url, headers=headers, json={"query": query, "variables": {"search": title}})
    if response.status_code == 200:
        return response.json().get("data", {}).get("Media", {})
    return {}

def normalize_title(title):
    return re.sub(r'\W+', '', title or '').lower()

CACHE_PATH = os.path.expanduser("~/custom-ani-cli/hash-to-anilist.json")

def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def main():
    history = load_history()
    cache_list = load_cache()
    cache = {entry["hash"]: entry for entry in cache_list}


    for entry in history:
        if entry["id"] in seen_ids:
            continue
        seen_ids.add(entry["id"])

        item = cache.get(entry["id"])
        if not item:
            ani = fetch_anilist_data(entry["raw_title"])
            if not ani:
                continue
            item = {
                    "title": entry["raw_title"],
                    "romaji": ani.get("title", {}).get("romaji", ""),
                    "english": ani.get("title", {}).get("english", ""),
                    "anilist_id": ani.get("id"),
                    "status": ani.get("status"),
                    "episodes": ani.get("episodes")
                }

            cache[entry["id"]] = item
            updated = True

        display_title = item["english"] if item["english"] and item["english"].lower() != item["romaji"].lower() else item["romaji"]
        ep_total = item.get("episodes") or entry["total_eps"]
        print(f"{entry['id']}\t{display_title} - episode {entry['watched']}/{ep_total}")

    if updated:
        save_cache(cache)



if __name__ == "__main__":
    main()


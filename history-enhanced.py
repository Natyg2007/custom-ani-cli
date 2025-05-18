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

def main():
    history = load_history()
    for entry in history:
        ani = fetch_anilist_data(entry["raw_title"])
        if not ani:
            continue

        ep_total = ani.get("episodes") or entry["total_eps"]
        status = ani.get("status", "RELEASING")
        romaji = ani["title"].get("romaji", "").strip()
        english = ani["title"].get("english", "").strip()
        
        if not english or english.lower() == romaji.lower():
            display = romaji
        else:
            display = f"{english} ({romaji})"
      #  if entry["watched"] == ep_total and status == "FINISHED":
       #     continue  # skip finished and completed
        print(f"{entry['id']}\t{display} - episode {entry['watched']}/{ep_total}")

if __name__ == "__main__":
    main()


import os
import datetime
import re
import sys
import time
import random
from googleapiclient.discovery import build
from google import genai  
from google.genai import types
from google.api_core import exceptions

# --- CONFIGURATION & SAFETY CHECKS ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not YOUTUBE_API_KEY:
    print("❌ Error: YOUTUBE_API_KEY is missing from environment variables.")
    print("Run: export YOUTUBE_API_KEY='your_key_here'")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY is missing from environment variables.")
    print("Run: export GEMINI_API_KEY='your_key_here'")
    sys.exit(1)

OUTPUT_DIR = "content/posts"

QUERIES = [
    "Jagjit Singh sad ghazal",
    "Coke Studio separation songs",
    "Arijit Singh sad lyrical",
    "Mehdi Hassan ghazal",
    "best urdu poetry status"
]

# --- SETUP CLIENTS ---
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# NEW: Initialize the new GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

def get_existing_video_ids():
    """Scans existing markdown files to find video IDs we already have."""
    existing_ids = set()
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".md"):
            with open(os.path.join(OUTPUT_DIR, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'video_id: ["\']?([a-zA-Z0-9_-]+)["\']?', content)
                if match:
                    existing_ids.add(match.group(1))
    return existing_ids

# Backup descriptions in case of any error
BACKUP_QUOTES = [
    "A melody that speaks the language of silence and memory.",
    "Some songs are not just music; they are echoes of a person we miss.",
    "In every note, there is a hidden letter to someone who is no longer here.",
    "Distance is just a test to see how far love can travel.",
    "The heart remembers what the mind tries to forget.",
    "A beautiful rendition that captures the hollow feeling of separation."
]

def generate_emotional_text(title):
    """Asks Gemma 3 for a poem, with backup text fallback."""
    print(f"   ... Asking AI (Gemma 3) about '{title}'")
    
    prompt = (
        f"Write a very short, 2-sentence poetic reflection in English about the song '{title}'. "
        f"The theme is longing and separation. Do not use hashtags."
    )
    
    try:
        # SWITCHING TO GEMMA 3 (14.4K Daily Quota)
        # We use 'gemma-3-12b-it' which is the Instruction-Tuned version of the model on your list.
        response = client.models.generate_content(
            model='gemma-3-12b-it', 
            contents=prompt,
        )
        return response.text.strip().replace('"', "'")

    except Exception as e:
        print(f"⚠️ AI Error (Using backup): {e}")
        return random.choice(BACKUP_QUOTES)

def generate_emotional_text2(title):
    """Asks Gemini to write a short poetic intro with retry logic."""
    print(f"   ... Asking AI about '{title}'")
    
    prompt = (
        f"Write a very short, 2-sentence poetic reflection in English about the song '{title}'. "
        f"The theme is longing and separation. Do not use hashtags. "
        f"Make it sound unique and different from previous ones."
    )
    
    # Try up to 3 times
    for attempt in range(3):
        try:
            # Use the STABLE model (gemini-flash-latest = 1.5 Flash)
            # This one has a generous free tier.
            response = client.models.generate_content(
                model='gemini-flash-latest', 
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                )
            )
            
            # If successful, wait 2 seconds (to be nice to the API) and return
            time.sleep(2)
            return response.text.strip().replace('"', "'")
            
        except exceptions.ResourceExhausted:
            # If we hit a rate limit, wait 30 seconds and try again
            wait_time = 30
            print(f"⚠️ Rate limit hit. Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
            continue # Try the loop again
            
        except Exception as e:
            # Any other error? Print it and return default.
            print(f"❌ AI Error: {e}")
            return "A melody that speaks the language of silence and memory."

    # If it failed 3 times, give up
    print("❌ Failed after 3 retries.")
    return "A melody that speaks the language of silence and memory."

def fetch_and_save_videos():
    existing_ids = get_existing_video_ids()
    print(f"Found {len(existing_ids)} existing videos.")

    for query in QUERIES:
        print(f"Searching for: {query}...")
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=10, 
            order="date"
        )
        response = request.execute()

        for item in response['items']:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            
            if video_id in existing_ids:
                print(f"Skipping duplicate: {title}")
                continue

            print(f"Processing new video: {title}")
            ai_description = generate_emotional_text(title)
            
            # Create a clean filename
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            # Limit filename length to avoid filesystem errors
            slug = slug[:50] 
            date_str = datetime.date.today().isoformat()
            
            markdown_content = f"""---
title: "{title}"
date: {date_str}
video_id: "{video_id}"
cover:
    image: "{thumbnail_url}"
    alt: "{title}"
    relative: false 
tags: ["music", "separation", "{query.split()[0]}"]
draft: false
---

{ai_description}

{{{{< youtube {video_id} >}}}}
"""
            
            filename = f"{OUTPUT_DIR}/{date_str}-{slug}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Saved: {filename}")
            existing_ids.add(video_id)
            
            print("Sleeping 15 second to respect the rate limit...")
            time.sleep(15)

if __name__ == "__main__":
    fetch_and_save_videos()

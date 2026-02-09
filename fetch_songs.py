import os
import datetime
import re
import sys
import time
import random
from googleapiclient.discovery import build
from google import genai
from google.genai import types

# --- CONFIGURATION ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Safety check
if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
    print("❌ Error: API Keys are missing. Export them first.")
    sys.exit(1)

OUTPUT_DIR = "content/posts"
SHAYARI_DIR = "content/shayari"

QUERIES = [
    "Jagjit Singh sad ghazal",
    "Coke Studio separation songs",
    "Arijit Singh sad lyrical",
    "Mehdi Hassan ghazal",
    "Mohd Rafi sad songs",
    "Ali Sethi sad songs",
    "Nayyara Noor ghazal",
    "sad bollywood songs lyrical",
    "heartbreak songs india lyrical video",
    "lonely night hindi songs coke studio"
]

POETS = [
    "Mirza Ghalib",
    "Jaun Elia",
    "Faiz Ahmed Faiz",
    "Parveen Shakir",
    "Ahmad Faraz",
    "Rahat Indori",
    "Sahir Ludhianvi",
    "Amrita Pritam",
    "Nida Fazli",
    "Gulzar",
    "Rumi"
]

# --- SETUP CLIENTS ---
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

# Backup descriptions in case of any error
BACKUP_QUOTES = [
    "A melody that speaks the language of silence and memory.",
    "Some songs are not just music; they are echoes of a person we miss.",
    "In every note, there is a hidden letter to someone who is no longer here.",
    "Distance is just a test to see how far love can travel.",
    "The heart remembers what the mind tries to forget.",
    "A beautiful rendition that captures the hollow feeling of separation."
]

PROMPTS_LIST = [
    # Vibe 1: The Philosopher (Deep & Abstract)
    """
    Write a short, philosophical reflection on separation based on this song: '{title}'.
    Focus on the concept of time and memory.
    Do NOT use the words: echo, tapestry, symphony, silent.
    Keep it under 50 words.
    """,

    # Vibe 2: The Gen-Z Friend (Casual & Relatable)
    """
    Write a short, relatable caption for this sad song: '{title}'.
    Write it like a text message to a friend who is heartbroken.
    Use lowercase, simple language. No flowery poetry.
    Keep it under 30 words.
    """,

    # Vibe 3: The Music Critic (Analytical & Cold)
    """
    Analyze the mood of the song '{title}' in one sharp sentence.
    Focus on the lyrics and the feeling of loss.
    Be direct and dry. No metaphors.
    """,

    # Vibe 4: The Storyteller (Visual & Specific)
    """
    Describe a specific scene that fits this song: '{title}'.
    Example: 'Sitting on a park bench in December waiting for a bus that never comes.'
    Do not mention the song itself, just the scene.
    """
]
# --- HELPER FUNCTIONS ---

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:50]

# --- SHAYARI GENERATION ---
def fetch_and_save_shayari():
    ensure_dir(SHAYARI_DIR)
    
    # Pick 2 random poets
    selected_poets = random.sample(POETS, 2)
    
    for poet in selected_poets:
        print(f"✍️  Asking AI for a couplet by {poet}...")
        
        prompt = (
            f"Recall a famous, heart-touching 2-line Sher (couplet) by {poet}. "
            f"Theme: Separation (Hijr) or Melancholy.\n"
            f"Output strictly in this format with '||' separators:\n"
            f"ORIGINAL_SCRIPT (In Urdu/Devanagari) || ROMAN_URDU || ENGLISH_TRANSLATION || THEME_ONE_WORD"
        )
        
        try:
            response = client.models.generate_content(
                model='gemma-3-12b-it',
                contents=prompt
            )
            
            text = response.text.strip()
            
            if "||" in text:
                parts = text.split("||")
                # Parse all 4 parts
                original_script = parts[0].strip().replace('"', '')
                roman_urdu = parts[1].strip().replace('"', '')
                translation = parts[2].strip().replace('"', '')
                theme = parts[3].strip().replace('"', '')
                
                slug = slugify(roman_urdu[:30])
                date_str = datetime.date.today().isoformat()
                filename = f"{SHAYARI_DIR}/{date_str}-{slug}.md"
                
                if os.path.exists(filename):
                    print(f"   Skipping duplicate Shayari: {slug}")
                    continue

                # We save the original script in the Markdown body with a special class
                markdown_content = f"""---
title: "{poet} on {theme}"
date: {date_str}
author: "{poet}"
tags: ["shayari", "urdu", "{theme.lower()}", "{slugify(poet)}"]
draft: false
layout: "shayari" 
---

<div class="shayari-original">
{original_script}
</div>

> *{roman_urdu}*

### Translation
{translation}
"""
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"   Saved Shayari: {filename}")
                
            else:
                print(f"   ⚠️ AI formatting error for {poet}. Skipping.")

        except Exception as e:
            print(f"   ⚠️ Shayari Error: {e}")
        
        time.sleep(2)

def clean_title_fallback(raw_title):
    """
    Backup method: Uses Regex to remove emojis, hashtags, and text in brackets () [].
    Example: "Song Name (Official Video) 😭 #sad" -> "Song Name"
    """
    # Remove emojis (non-ascii characters)
    clean = raw_title.encode('ascii', 'ignore').decode('ascii')
    # Remove hashtags
    clean = re.sub(r'#\w+', '', clean)
    # Remove text in brackets () or [] or ||
    clean = re.sub(r'\s*[\[\(\|].*?[\)\]\|]', '', clean)
    # Remove extra spaces
    clean = " ".join(clean.split())
    return clean

def generate_content(raw_title):
    """
    Asks AI for a clean title and description.
    Includes checks to ensure it doesn't return placeholder text.
    """
    print(f"   ... Asking AI to clean & describe '{raw_title}'")
    
    prompt = random.choice(PROMPTS_LIST)
    
    try:
        response = client.models.generate_content(
            model='gemma-3-12b-it', 
            contents=prompt,
        )
        
        text = response.text.strip()
        
        # Split by the separator
        if "||" in text:
            parts = text.split("||")
            clean_title = parts[0].strip().replace('"', '')
            description = parts[1].strip().replace('"', '')
            
            # SANITY CHECK: Did AI return the literal instruction?
            if "CLEAN_TITLE" in clean_title or len(clean_title) < 3:
                print("   ⚠️ AI returned bad title. Using fallback.")
                return clean_title_fallback(raw_title), description
                
            return clean_title, description
        else:
            # AI forgot the separator? Use the whole text as description, fallback title
            return clean_title_fallback(raw_title), text

    except Exception as e:
        print(f"   ⚠️ AI Error: {e}. Using fallback.")
        return clean_title_fallback(raw_title), random.choice(BACKUP_QUOTES)
        
        
def get_existing_video_ids():
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

def fetch_and_save_videos():
    existing_ids = get_existing_video_ids()
    print(f"Found {len(existing_ids)} existing videos.")

    for query in QUERIES:
        print(f"Searching for: {query}...")
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            videoEmbeddable="true",
            regionCode="IN",
            maxResults=5, 
            order="relevance" # Changed to find better quality titles
        )
        response = request.execute()

        for item in response['items']:
            video_id = item['id']['videoId']
            raw_title = item['snippet']['title']
            
            if video_id in existing_ids:
                print(f"Skipping duplicate: {raw_title[:30]}...")
                continue

            # --- CALL THE NEW AI FUNCTION ---
            final_title, ai_description = generate_content(raw_title)
            print(f"✨ Cleaned Title: {final_title}")
            
            # Slugify the CLEAN title, not the raw one
            slug = re.sub(r'[^a-z0-9]+', '-', final_title.lower()).strip('-')[:50]
            date_str = datetime.date.today().isoformat()
            
            # High Quality Thumbnail
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            
            markdown_content = f"""---
title: "{final_title}"
date: {date_str}
video_id: "{video_id}"
cover:
    image: "{thumbnail_url}"
    alt: "{final_title}"
    relative: false
tags: ["music", "separation", "{query.split()[0]}"]
draft: false
---

{ai_description}

{{{{< youtube {video_id} >}}}}
"""
            
            filename = f"{OUTPUT_DIR}/{date_str}-{slug}-{video_id}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"Saved: {filename}")
            existing_ids.add(video_id)
            
            # Sleep to be safe
            time.sleep(2)

if __name__ == "__main__":
    print("--- 🎵 Fetching Songs ---")
    fetch_and_save_videos()
    print("\n--- ✍️  Fetching Shayari ---")
    fetch_and_save_shayari()

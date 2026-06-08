"""
Caption Generator — Uses Groq API (100% FREE, very fast)
Get free API key at: https://console.groq.com/
Models: llama3-70b-8192 (free), mixtral-8x7b (free)
"""

import requests
import json
import random

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Tone rotation to keep content fresh
CAPTION_TONES = [
    "mysterious and flirty",
    "confident and bold",
    "dreamy and poetic",
    "playful and teasing",
    "empowering and fierce",
    "soft and romantic",
    "adventurous and free-spirited",
]

HASHTAG_SETS = [
    "#aimodel #artificialintelligence #digitalart #aifashion #aibeauty #virtualinfluencer #aigirl #fashion #style #beauty",
    "#aiinfluencer #generativeart #stableai #aiartwork #digitalmodel #aicreator #instafashion #photooftheday #gorgeous #stunning",
    "#virtualmodel #aigenerated #futureofart #digitalbeauty #aiportrait #contentcreator #fashionista #lifestyle #aesthetic #viral",
    "#aiphotography #digitalfashion #synthwave #aiart #beautifulai #techbeauty #ailife #instadaily #trending #explore",
]

def generate_caption(theme: dict, groq_api_key: str) -> str:
    """Generate an engaging caption + hashtags using Groq's free LLM."""

    tone = random.choice(CAPTION_TONES)
    hashtags = random.choice(HASHTAG_SETS)

    system_prompt = """You are a social media expert who writes viral Instagram captions for an AI influencer.
Your captions are short, punchy, engaging — they stop the scroll.
Never mention being AI unless asked. Write as a real confident woman would.
Always end with a question or call-to-action to boost comments.
Keep it under 150 characters for the main caption (hashtags separate).
No emojis overload — max 3 emojis."""

    user_prompt = f"""Write an Instagram caption for this photo:
- Style: {theme['style']}
- Setting: {theme['setting']}  
- Vibe: {theme['vibe']}
- Tone: {tone}

Return ONLY the caption text (no hashtags, no quotes, no explanation).
Make it unforgettable."""

    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.9,
        }

        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            caption_text = data["choices"][0]["message"]["content"].strip()
            full_caption = f"{caption_text}\n\n{hashtags}"
            return full_caption
        else:
            print(f"Groq API error: {response.status_code} — {response.text}")
            return fallback_caption(theme, hashtags)

    except Exception as e:
        print(f"Caption generation error: {e}")
        return fallback_caption(theme, hashtags)

def fallback_caption(theme: dict, hashtags: str) -> str:
    """Backup captions if API fails."""
    fallbacks = [
        f"Living in my own world. ✨ What's your escape?\n\n{hashtags}",
        f"Not your average day. 🔥 Drop a ❤️ if you vibe with this.\n\n{hashtags}",
        f"She didn't ask for permission. 💫 Would you?\n\n{hashtags}",
        f"The version of me you weren't ready for. Which look next? 👀\n\n{hashtags}",
    ]
    import random
    return random.choice(fallbacks)

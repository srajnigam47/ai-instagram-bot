"""
Image Generator — Uses Hugging Face Inference API (FREE)
Model: stable-diffusion-xl-base-1.0 or similar free models
"""

import requests
import base64
import time
import io

# Best free models on Hugging Face for realistic AI girls
HF_MODELS = [
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
    "Lykon/dreamshaper-8",          # Great for realistic portraits
    "SG161222/Realistic_Vision_V6.0_B1_noVAE",
]

def build_prompt(theme: dict) -> str:
    """Build a detailed prompt for a consistent AI girl character."""
    base_character = (
        "beautiful young woman, dark hair, hazel eyes, perfect skin, "
        "natural makeup, photorealistic, hyperdetailed face, "
    )
    return (
        f"{base_character}"
        f"{theme['style']}, {theme['setting']}, "
        f"{theme['vibe']} expression, "
        "professional photography, 8k uhd, sharp focus, "
        "cinematic lighting, bokeh background, "
        "Instagram influencer photo, magazine quality"
    )

def build_negative_prompt() -> str:
    return (
        "ugly, deformed, disfigured, blurry, low quality, "
        "watermark, text, extra limbs, bad anatomy, "
        "cartoon, anime, illustration, painting"
    )

def generate_with_huggingface(prompt: str, negative_prompt: str, api_key: str) -> bytes | None:
    """Call Hugging Face Inference API — free tier."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 1024,
            "height": 1024,
        }
    }

    for model in HF_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        print(f"  Trying model: {model}")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
                print(f"  ✅ Success with {model}")
                return response.content
            elif response.status_code == 503:
                # Model loading, wait and retry once
                print(f"  ⏳ Model loading, waiting 20s...")
                time.sleep(20)
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                if response.status_code == 200:
                    return response.content
            else:
                print(f"  ⚠️ {model} returned {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error with {model}: {e}")
            continue

    return None

def upload_to_imgbb(image_bytes: bytes, api_key: str) -> str | None:
    """
    Upload image to ImgBB (free image hosting).
    Instagram needs a public URL — ImgBB provides one for free.
    Get free API key at: https://api.imgbb.com/
    """
    try:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": b64_image},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"]["url"]
        else:
            print(f"ImgBB upload failed: {response.status_code} — {response.text}")
            return None
    except Exception as e:
        print(f"ImgBB upload error: {e}")
        return None

def generate_image(theme: dict, hf_api_key: str, imgbb_api_key: str) -> str | None:
    """Full pipeline: generate → upload → return public URL."""
    prompt = build_prompt(theme)
    negative_prompt = build_negative_prompt()

    print(f"  Prompt: {prompt[:100]}...")

    image_bytes = generate_with_huggingface(prompt, negative_prompt, hf_api_key)
    if not image_bytes:
        return None

    print("  Uploading to ImgBB...")
    public_url = upload_to_imgbb(image_bytes, imgbb_api_key)
    return public_url

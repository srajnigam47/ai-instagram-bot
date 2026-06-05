"""
Image Generator — Uses Hugging Face Inference API (FREE)
"""

import requests
import base64
import time

HF_BASE = "https://router.huggingface.co/hf-inference/models"

# Models with their supported payload styles
# "flux" = no negative_prompt, simple inputs only
# "sd"   = supports negative_prompt + parameters
HF_MODELS = [
    ("black-forest-labs/FLUX.1-schnell", "flux"),
    ("black-forest-labs/FLUX.1-dev",     "flux"),
    ("stabilityai/stable-diffusion-2-1", "sd"),
    ("Lykon/dreamshaper-xl-lightning",   "sd"),
]

def build_prompt(theme: dict) -> str:
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
    headers = {"Authorization": f"Bearer {api_key}"}

    for model, style in HF_MODELS:
        url = f"{HF_BASE}/{model}"
        print(f"  Trying model: {model}")

        if style == "flux":
            payload = {"inputs": prompt}
        else:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                    "width": 1024,
                    "height": 1024,
                }
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            content_type = response.headers.get("content-type", "")

            if response.status_code == 200 and content_type.startswith("image"):
                print(f"  Success with {model}")
                return response.content
            elif response.status_code == 503:
                print(f"  Model loading, waiting 20s...")
                time.sleep(20)
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                if response.status_code == 200:
                    return response.content
            else:
                print(f"  {model} returned {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"  Error with {model}: {e}")
            continue

    return None

def upload_to_imgbb(image_bytes: bytes, api_key: str) -> str | None:
    try:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": b64_image},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["data"]["url"]
        else:
            print(f"ImgBB upload failed: {response.status_code} — {response.text}")
            return None
    except Exception as e:
        print(f"ImgBB upload error: {e}")
        return None

def generate_image(theme: dict, hf_api_key: str, imgbb_api_key: str) -> str | None:
    prompt = build_prompt(theme)
    negative_prompt = build_negative_prompt()
    print(f"  Prompt: {prompt[:100]}...")
    image_bytes = generate_with_huggingface(prompt, negative_prompt, hf_api_key)
    if not image_bytes:
        return None
    print("  Uploading to ImgBB...")
    return upload_to_imgbb(image_bytes, imgbb_api_key)

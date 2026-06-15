"""
Image Generator — Hugging Face Inference API (FREE)
Prompts use natural photography language to minimize the "AI look".
"""

import requests
import base64
import time

HF_BASE = "https://router.huggingface.co/hf-inference/models"

HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "black-forest-labs/FLUX.1-dev",
]

# Rotate character descriptions so the "face" varies day to day
CHARACTERS = [
    "A woman in her mid-twenties with long dark wavy hair past her shoulders, warm olive skin, dark almond eyes, full lips",
    "A young woman with straight black hair cut to her collarbone, angular jawline, tan skin, deep brown eyes",
    "A woman with long dark hair and subtle auburn highlights, heart-shaped face, caramel skin, hazel eyes",
    "A mid-twenties woman with thick dark hair pulled half-up, light brown eyes, golden tan skin, soft features",
    "A young woman with dark hair in loose waves, sharp cheekbones, bronzed skin, almond-shaped eyes, confident look",
]

CAMERA_STYLES = [
    "Canon EOS R5, 85mm portrait lens, f/1.8, shallow depth of field",
    "Sony A7R IV, 50mm, natural window light",
    "Leica Q2, candid moment, warm afternoon light",
    "shot on film, Kodak Portra 400, slightly warm tones",
    "editorial photography, clean professional lighting",
]

OUTFITS = {
    "fashion editorial":  ["fitted blazer open over a simple top, tailored trousers", "off-shoulder silk blouse, high-waist jeans", "slip dress with delicate gold jewelry"],
    "fitness aesthetic":  ["fitted sports bra and high-waist leggings", "oversized athletic hoodie, biker shorts", "crop top and track pants"],
    "beach lifestyle":    ["bikini top with linen shorts and an open shirt", "one-piece swimsuit", "flowing sundress, barefoot"],
    "street fashion":     ["leather jacket, crop top, cargo pants", "oversized hoodie, bike shorts, chunky sneakers", "vintage tee, mini skirt, ankle boots"],
    "cozy aesthetic":     ["oversized knit sweater, straight-leg jeans", "cozy turtleneck, wide-leg pants", "soft cardigan over a simple dress"],
    "glamour shot":       ["sequin slip dress", "form-fitting bodycon dress, minimal jewelry", "sleek satin gown"],
    "travel influencer":  ["linen co-ord set", "floral midi dress, straw hat", "cropped blazer, wide-leg trousers"],
    "party ready":        ["backless mini dress", "silky two-piece set", "embellished corset top, tailored pants"],
}

def _pick(lst, seed):
    return lst[seed % len(lst)]

def build_prompt(theme: dict, seed: int = 0) -> str:
    char   = _pick(CHARACTERS, seed)
    camera = _pick(CAMERA_STYLES, seed + 1)
    outfit = _pick(OUTFITS.get(theme["style"], ["stylish casual outfit"]), seed + 2)

    return (
        f"{char}. She is wearing {outfit}. "
        f"She is at {theme['setting']}, {theme['vibe']} mood, relaxed natural pose. "
        f"{camera}. Instagram lifestyle photo."
    )

def build_shot_prompt(theme: dict, shot: int, seed: int = 0) -> str:
    char   = _pick(CHARACTERS, seed)
    camera = _pick(CAMERA_STYLES, seed + shot + 1)
    outfit = _pick(OUTFITS.get(theme["style"], ["stylish casual outfit"]), seed)

    shot_angles = [
        f"full body shot showing her complete look, {theme['setting']}, golden hour light",
        "close-up portrait from the shoulders up, looking directly at camera, soft natural smile, beautiful bokeh background",
        f"mid shot from the waist up, candid moment, looking slightly to the side, {theme['setting']}",
    ]
    angle = _pick(shot_angles, shot)

    return (
        f"{char}, wearing {outfit}. {angle}. "
        f"{theme['vibe'].capitalize()} expression. {camera}."
    )

def generate_hf_image(prompt: str, api_key: str, width: int = 768, height: int = 1344) -> bytes | None:
    headers = {"Authorization": f"Bearer {api_key}"}

    for model in HF_MODELS:
        url = f"{HF_BASE}/{model}"
        print(f"  Trying {model.split('/')[-1]}...")

        # Try with portrait dimensions first
        for payload in [
            {"inputs": prompt, "parameters": {"width": width, "height": height}},
            {"inputs": prompt},
        ]:
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=120)
                ct = r.headers.get("content-type", "")
                if r.status_code == 200 and ct.startswith("image"):
                    return r.content
                elif r.status_code == 503:
                    print("  Model loading, retrying in 20s...")
                    time.sleep(20)
                    r = requests.post(url, headers=headers, json=payload, timeout=120)
                    if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                        return r.content
                    break
                elif r.status_code in (400, 422):
                    # Parameters not supported — try without
                    if "parameters" in payload:
                        continue
                    print(f"  {model.split('/')[-1]}: HTTP {r.status_code}")
                    break
                else:
                    print(f"  {model.split('/')[-1]}: HTTP {r.status_code}")
                    break
            except Exception as e:
                print(f"  HF error: {e}")
                break

    return None

def upload_to_imgbb(image_bytes: bytes, api_key: str) -> str | None:
    try:
        b64 = base64.b64encode(image_bytes).decode()
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": api_key, "image": b64},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["data"]["url"]
        print(f"  ImgBB upload failed: {r.status_code}")
        return None
    except Exception as e:
        print(f"  ImgBB error: {e}")
        return None

def generate_image(theme: dict, hf_api_key: str, imgbb_api_key: str, seed: int = 0) -> str | None:
    prompt = build_prompt(theme, seed)
    print(f"  Prompt: {prompt[:120]}...")
    image_bytes = generate_hf_image(prompt, hf_api_key)
    if not image_bytes:
        return None
    print("  Uploading to ImgBB...")
    return upload_to_imgbb(image_bytes, imgbb_api_key)

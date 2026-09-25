"""
Image Generator — Pollinations.ai (FREE, no API key required)
Prompts use natural photography language to minimize the "AI look".

Note: Hugging Face's free `hf-inference` provider stopped hosting
FLUX/SD serverless inference in mid-2026 (models now route through paid
providers like fal-ai/replicate only). Pollinations.ai is a genuinely
free alternative — anonymous requests work with a small watermark;
set POLLINATIONS_TOKEN (free signup at https://auth.pollinations.ai)
to remove it and raise the rate limit.
"""

import os
import io
import base64
import requests
import urllib.parse
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

# The free Pollinations tier caps actual output around ~0.6MP no matter
# what width/height is requested (measured: asking for 1080x1920 returns
# ~580x1015). Upscale before posting so Instagram doesn't have to.
TARGET_WIDTH = 1080

# Rotate character descriptions so multiple distinct "models" appear, not one repeated face
CHARACTERS = [
    "An Indian woman in her mid-twenties with long dark wavy hair past her shoulders, warm wheatish skin, dark almond eyes, full lips, curvy figure",
    "A young Indian woman with straight black hair cut to her collarbone, angular jawline, tan skin, deep brown eyes, athletic toned figure",
    "An Indian woman with long dark hair and subtle brown highlights, heart-shaped face, caramel skin, hazel eyes, hourglass figure",
    "A mid-twenties Indian woman with thick dark hair pulled half-up, light brown eyes, golden tan skin, soft features, curvy figure",
    "A young Indian woman with dark hair in loose waves, sharp cheekbones, bronzed skin, almond-shaped eyes, confident look, hourglass figure",
    "A South Indian woman in her mid-twenties, long straight jet-black hair, deep bronze skin, large expressive dark eyes, curvy figure",
    "A Punjabi woman with wavy chestnut-highlighted hair, fair wheatish skin, sharp features, hazel eyes, tall slender figure",
    "A Bengali woman with dark hair in a low bun, warm olive skin, soft round face, expressive kohl-lined eyes, curvy figure",
    "An Indian woman with shoulder-length layered hair, sun-kissed tan skin, high cheekbones, bright smile, athletic curvy figure",
    "A young Indian woman with long dark hair, deep brown skin, striking features, confident expression, petite curvy figure",
]

CAMERA_STYLES = [
    "shot on iPhone 15 Pro front camera, mirror selfie, natural lighting, slightly casual framing",
    "shot on iPhone, candid phone photo, natural light, realistic phone camera grain",
    "phone camera selfie, casual pose, warm natural lighting, authentic amateur photo feel",
    "shot on iPhone, natural daylight, candid unposed moment",
    "phone camera quality, warm ambient lighting, casual selfie angle",
]

OUTFITS = {
    "beach lifestyle":      ["colorful triangle bikini with a sheer sarong wrap", "one-piece swimsuit with a light cover-up", "halter bikini top and high-waist bikini bottoms"],
    "poolside glam":        ["metallic one-piece swimsuit", "high-cut bikini with gold jewelry", "cut-out one-piece swimsuit"],
    "bikini beach day":     ["bright bikini with a straw hat", "ribbed bikini set", "classic red bikini"],
    "tropical golden hour": ["flowy beach dress over a bikini", "crochet bikini set", "linen beach cover-up"],
    "fitness aesthetic":    ["fitted sports bra and high-waist leggings", "athletic two-piece set", "crop top and bike shorts"],
    "resort vacation":      ["silky beach kaftan", "linen co-ord set", "strapless sundress"],
    "glamour swimwear":     ["sculpted one-piece swimsuit", "high-shine bikini set", "plunge one-piece with gold accents"],
    "sunset beach party":   ["boho bikini with layered necklaces", "backless swim romper", "fringe bikini set"],
}

SAFETY_SUFFIX = "confident swimwear/fashion photography, no nudity, no exposed nipples or genitals, not sexually explicit"

def _pick(lst, seed):
    return lst[seed % len(lst)]

def build_prompt(theme: dict, seed: int = 0) -> str:
    char   = _pick(CHARACTERS, seed)
    camera = _pick(CAMERA_STYLES, seed + 1)
    outfit = _pick(OUTFITS.get(theme["style"], ["stylish casual outfit"]), seed + 2)

    return (
        f"{char}. She is wearing {outfit}. "
        f"She is at {theme['setting']}, {theme['vibe']} mood, relaxed natural pose. "
        f"{camera}. Candid real-life Instagram photo, not a professional photoshoot, "
        f"authentic and unfiltered feel. {SAFETY_SUFFIX}."
    )

def build_shot_prompt(theme: dict, shot: int, seed: int = 0) -> str:
    char   = _pick(CHARACTERS, seed)
    camera = _pick(CAMERA_STYLES, seed + shot + 1)
    outfit = _pick(OUTFITS.get(theme["style"], ["stylish casual outfit"]), seed)

    shot_angles = [
        f"full body shot showing her complete look, {theme['setting']}, golden hour light",
        "mirror selfie, phone visible in reflection, casual pose, looking at her own reflection",
        f"mid shot from the waist up, candid moment, looking slightly to the side, {theme['setting']}",
    ]
    angle = _pick(shot_angles, shot)

    return (
        f"{char}, wearing {outfit}. {angle}. "
        f"{theme['vibe'].capitalize()} expression. {camera}. {SAFETY_SUFFIX}."
    )

def generate_hf_image(prompt: str, api_key: str, width: int = 768, height: int = 1344) -> bytes | None:
    """Generate an image via Pollinations.ai. `api_key` kept for call-site
    compatibility but unused — auth is via POLLINATIONS_TOKEN if set."""
    token = os.environ.get("POLLINATIONS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "model": "flux",
        "nologo": "true",
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=120)
        ct = r.headers.get("content-type", "")
        if r.status_code == 200 and ct.startswith("image"):
            return r.content
        print(f"  Pollinations: HTTP {r.status_code} — {r.text[:200]}")
    except Exception as e:
        print(f"  Pollinations error: {e}")

    return None

FAL_MODEL_URL = "https://fal.run/fal-ai/flux/dev"

def generate_fal_image(prompt: str, width: int = 768, height: int = 1344) -> bytes | None:
    """Generate via fal.ai (real FLUX.1-dev), if FAL_API_KEY is set. Paid
    (small per-image cost), not free — but a leftover key already exists
    in this repo's secrets from an earlier version of the project, so
    worth trying before asking for anything new. Falls through safely
    if the key is invalid/expired or out of credit."""
    api_key = os.environ.get("FAL_API_KEY")
    if not api_key:
        return None
    try:
        r = requests.post(
            FAL_MODEL_URL,
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "image_size": {"width": width, "height": height},
                "num_images": 1,
            },
            timeout=90,
        )
        if r.status_code != 200:
            print(f"  fal.ai: HTTP {r.status_code} — {r.text[:200]}")
            return None
        images = r.json().get("images", [])
        if not images:
            print("  fal.ai: no images in response")
            return None
        img_r = requests.get(images[0]["url"], timeout=60)
        if img_r.status_code == 200:
            return img_r.content
        print(f"  fal.ai: image download failed: {img_r.status_code}")
        return None
    except Exception as e:
        print(f"  fal.ai error: {e}")
        return None

CLOUDFLARE_MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"

def generate_cloudflare_image(prompt: str, width: int = 768, height: int = 1344) -> bytes | None:
    """Generate via Cloudflare Workers AI (real SDXL), if CLOUDFLARE_ACCOUNT_ID
    and CLOUDFLARE_API_TOKEN are set. Genuinely free permanent daily quota
    (10k neurons/day, no card required) from a stable major provider —
    unlike Gemini's free image tier, which got discontinued. 768x1344 is
    one of SDXL's native trained resolution buckets (closest to 9:16)."""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account_id or not api_token:
        return None
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{CLOUDFLARE_MODEL}"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_token}"},
            json={"prompt": prompt, "width": width, "height": height},
            timeout=60,
        )
        if r.status_code != 200:
            print(f"  Cloudflare: HTTP {r.status_code} — {r.text[:200]}")
            return None
        ct = r.headers.get("content-type", "")
        if ct.startswith("image"):
            return r.content
        # Some Workers AI responses wrap the image as base64 JSON instead
        try:
            b64 = r.json().get("result", {}).get("image")
            if b64:
                return base64.b64decode(b64)
        except Exception:
            pass
        print(f"  Cloudflare: unexpected response (content-type={ct}) — {r.text[:200]}")
        return None
    except Exception as e:
        print(f"  Cloudflare error: {e}")
        return None

GEMINI_MODEL = "gemini-3.1-flash-image"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"

def generate_gemini_image(prompt: str) -> bytes | None:
    """Generate via Gemini (Nano Banana), if GEMINI_API_KEY is set. Real
    photorealism, but Google's own safety filter can refuse swimwear-
    adjacent prompts — caller should fall back to Pollinations on None."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        r = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        if r.status_code != 200:
            print(f"  Gemini: HTTP {r.status_code} — {r.text[:200]}")
            return None
        parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
        # No image part usually means a safety refusal explained in text
        refusal = " ".join(p.get("text", "") for p in parts if "text" in p)
        print(f"  Gemini returned no image (likely refused): {refusal[:200]}")
        return None
    except Exception as e:
        print(f"  Gemini error: {e}")
        return None

def generate_image_bytes(prompt: str, hf_api_key: str) -> tuple[bytes, str] | tuple[None, None]:
    """Try better sources first if configured, fall back to the
    always-available Pollinations source. Returns (bytes, source_name)."""
    fal_bytes = generate_fal_image(prompt)
    if fal_bytes:
        return fal_bytes, "fal"
    cf_bytes = generate_cloudflare_image(prompt)
    if cf_bytes:
        return cf_bytes, "cloudflare"
    gemini_bytes = generate_gemini_image(prompt)
    if gemini_bytes:
        return gemini_bytes, "gemini"
    pollinations_bytes = generate_hf_image(prompt, hf_api_key)
    if pollinations_bytes:
        return pollinations_bytes, "pollinations"
    return None, None

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

def process_image(image_bytes: bytes, target_width: int = TARGET_WIDTH, add_grain: bool = True) -> bytes:
    """Upscale + optional photographic post-processing. `add_grain` compensates
    for Pollinations' raw output being both low-res (~580px capped, see
    TARGET_WIDTH comment) and having a glossy/plastic "obviously AI" look
    that prompt wording alone couldn't shake (tested extensively). Skip it
    for Gemini output, which is already higher quality and doesn't need
    the fake-imperfection treatment."""
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if im.width < target_width:
            scale = target_width / im.width
            im = im.resize((target_width, round(im.height * scale)), Image.LANCZOS)

        if add_grain:
            arr = np.array(im).astype(np.float32)
            noise = np.random.normal(0, 6.5, arr.shape[:2])[:, :, None]
            im = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

            im = im.filter(ImageFilter.GaussianBlur(radius=0.6))
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
            im = ImageEnhance.Color(im).enhance(0.92)
            im = ImageEnhance.Contrast(im).enhance(0.97)

        out = io.BytesIO()
        im.save(out, format="JPEG", quality=92)
        return out.getvalue()
    except Exception as e:
        print(f"  Image processing error (using original): {e}")
        return image_bytes

def generate_image(theme: dict, hf_api_key: str, imgbb_api_key: str, seed: int = 0) -> str | None:
    prompt = build_prompt(theme, seed)
    print(f"  Prompt: {prompt[:120]}...")
    image_bytes, source = generate_image_bytes(prompt, hf_api_key)
    if not image_bytes:
        return None
    print(f"  Source: {source}")
    image_bytes = process_image(image_bytes, add_grain=(source == "pollinations"))
    print("  Uploading to ImgBB...")
    return upload_to_imgbb(image_bytes, imgbb_api_key)

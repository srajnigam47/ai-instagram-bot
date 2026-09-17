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
from PIL import Image

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

def upscale(image_bytes: bytes, target_width: int = TARGET_WIDTH) -> bytes:
    """Lanczos upscale to at least target_width — doesn't invent detail,
    but is a cleaner resize than what Instagram's client would do to a
    ~580px-wide source, and normalizes output size across posts."""
    try:
        im = Image.open(io.BytesIO(image_bytes))
        if im.width >= target_width:
            return image_bytes
        scale = target_width / im.width
        new_size = (target_width, round(im.height * scale))
        im = im.convert("RGB").resize(new_size, Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=92)
        return out.getvalue()
    except Exception as e:
        print(f"  Upscale error (using original): {e}")
        return image_bytes

def generate_image(theme: dict, hf_api_key: str, imgbb_api_key: str, seed: int = 0) -> str | None:
    prompt = build_prompt(theme, seed)
    print(f"  Prompt: {prompt[:120]}...")
    image_bytes = generate_hf_image(prompt, hf_api_key)
    if not image_bytes:
        return None
    image_bytes = upscale(image_bytes)
    print("  Uploading to ImgBB...")
    return upload_to_imgbb(image_bytes, imgbb_api_key)

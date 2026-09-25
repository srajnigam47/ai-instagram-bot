"""
Image Generator — Pollinations.ai / fal.ai / Cloudflare / Gemini

Generates photorealistic adult swimwear, beach, resort and lifestyle
photography with varied adult models, fuller/curvier body proportions,
fashion-forward swimwear, natural phone-camera aesthetics, and varied
locations/compositions.

The image pipeline tries configured providers in this order:
    1. fal.ai
    2. Cloudflare Workers AI
    3. Gemini
    4. Pollinations.ai

The generated images remain non-explicit:
no nudity, exposed nipples, or exposed genitals.
"""

import os
import io
import base64
import random
import requests
import urllib.parse

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

from text_overlay import add_overlay_text


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

# Instagram-friendly output width.
TARGET_WIDTH = 1080


# ---------------------------------------------------------------------------
# ADULT MODEL / CHARACTER DESCRIPTIONS
#
# These descriptions control the person's general appearance and body shape.
# The descriptions intentionally vary between models so the account doesn't
# produce the exact same face/body repeatedly.
# ---------------------------------------------------------------------------

CHARACTERS = [
    (
        "An adult Indian woman in her mid-twenties with long dark wavy hair, "
        "warm wheatish skin, dark almond eyes, full lips, a noticeably curvy "
        "voluptuous figure, defined waist, fuller hips, fuller thighs and "
        "naturally proportioned feminine curves"
    ),

    (
        "An adult Indian woman in her mid-twenties with straight black hair "
        "falling to her shoulders, tan skin, deep brown eyes, a curvy athletic "
        "build, strong legs, fuller thighs, rounded hips, defined waist and "
        "natural feminine proportions"
    ),

    (
        "An adult Indian woman in her mid-twenties with long dark hair and "
        "subtle brown highlights, caramel skin, hazel-brown eyes, a fuller "
        "hourglass figure, rounded hips, thick thighs, defined waist and "
        "naturally curvy proportions"
    ),

    (
        "An adult Indian woman in her mid-twenties with thick dark hair pulled "
        "half-up, golden tan skin, light brown eyes, soft facial features, "
        "a voluptuous curvy figure, fuller hips and thighs, defined waist and "
        "balanced natural proportions"
    ),

    (
        "An adult Indian woman in her mid-twenties with dark hair in loose "
        "waves, bronzed skin, sharp cheekbones, almond-shaped eyes, a glamorous "
        "hourglass figure, fuller thighs, rounded hips and a defined waist"
    ),

    (
        "An adult South Indian woman in her mid-twenties with long straight "
        "jet-black hair, deep bronze skin, large expressive dark eyes, a "
        "voluptuous curvy figure, fuller hips, fuller thighs and a defined waist"
    ),

    (
        "An adult Punjabi woman in her mid-twenties with wavy chestnut-highlighted "
        "hair, fair wheatish skin, sharp features, hazel eyes, a tall curvy "
        "figure, rounded hips, fuller thighs and a defined waist"
    ),

    (
        "An adult Bengali woman in her mid-twenties with dark hair in a low bun, "
        "warm olive skin, a soft round face, expressive kohl-lined eyes, a "
        "fuller curvy figure, rounded hips and strong feminine proportions"
    ),

    (
        "An adult Indian woman in her mid-twenties with shoulder-length layered "
        "hair, sun-kissed tan skin, high cheekbones, bright smile, an athletic "
        "curvy figure, fuller thighs, rounded hips and a defined waist"
    ),

    (
        "An adult Indian woman in her mid-twenties with long dark hair, deep "
        "brown skin, striking features, confident expression, a petite but "
        "noticeably curvy figure, rounded hips and fuller thighs"
    ),

    (
        "An adult Indian woman in her mid-twenties with glossy dark hair, "
        "golden-brown skin, expressive brown eyes, a glamorous fuller hourglass "
        "figure, rounded hips, fuller thighs and a defined waist"
    ),

    (
        "An adult Indian woman in her mid-twenties with long naturally wavy "
        "hair, warm brown skin, soft features, a fuller pear-shaped figure, "
        "prominent hips, fuller thighs and a relatively defined waist"
    ),
]


# ---------------------------------------------------------------------------
# CAMERA STYLES
# ---------------------------------------------------------------------------

CAMERA_STYLES = [
    (
        "shot on iPhone 15 Pro front camera, natural daylight, casual framing, "
        "realistic phone-camera detail"
    ),
    (
        "shot on iPhone, candid phone photo, natural sunlight, realistic "
        "phone-camera grain and slightly imperfect framing"
    ),
    (
        "phone camera selfie, warm natural lighting, casual authentic pose, "
        "realistic amateur Instagram photography"
    ),
    (
        "shot on iPhone, natural daylight, candid unposed moment, realistic "
        "skin texture and ordinary phone-camera optics"
    ),
    (
        "modern smartphone camera, warm ambient lighting, casual selfie angle, "
        "authentic social-media photography"
    ),
    (
        "high-quality smartphone portrait, natural outdoor light, realistic "
        "skin texture, subtle lens imperfections and candid composition"
    ),
]


# ---------------------------------------------------------------------------
# OUTFITS
#
# This is the main section to change if you want different swimwear styles.
# ---------------------------------------------------------------------------

OUTFITS = {
    "beach lifestyle": [
        "fashionable triangle bikini with a lightweight sheer sarong wrap",
        "minimalist two-piece bikini with a loose linen beach shirt",
        "high-cut bikini with a straw hat and lightweight beach cover-up",
        "stylish bikini set with a flowing translucent beach wrap",
    ],

    "poolside glam": [
        "glamorous high-cut bikini with delicate gold jewelry",
        "fashion-forward cut-out one-piece swimsuit with gold accessories",
        "luxury bikini set with oversized sunglasses and gold jewelry",
        "sleek high-waisted bikini with a silk cover-up",
    ],

    "bikini beach day": [
        "bright colorful bikini with a straw sun hat",
        "ribbed bikini set with a lightweight open beach shirt",
        "classic red bikini with sunglasses and a beach tote",
        "high-cut bikini set with a flowing beach cover-up",
    ],

    "tropical golden hour": [
        "flowy beach dress worn over a bikini",
        "crochet bikini set with a lightweight tropical cover-up",
        "minimalist bikini with a linen beach shirt",
        "glamorous bikini set with gold accessories",
    ],

    "fitness aesthetic": [
        "fitted sports bra and high-waist leggings",
        "athletic two-piece workout set",
        "crop top and fitted bike shorts",
        "stylish athletic set emphasizing a strong curvy physique",
    ],

    "resort vacation": [
        "silky beach kaftan over a stylish bikini",
        "linen co-ord set over swimwear",
        "strapless sundress with a bikini underneath",
        "luxury resort cover-up paired with a fashionable bikini",
    ],

    "glamour swimwear": [
        "sculpted one-piece swimsuit with elegant gold accents",
        "high-shine bikini set with luxury jewelry",
        "fashion-forward plunge one-piece with gold accessories",
        "minimalist high-cut bikini with statement sunglasses",
    ],

    "sunset beach party": [
        "boho bikini with layered necklaces",
        "stylish high-cut bikini with a lightweight beach shirt",
        "fringe-detail bikini set with layered jewelry",
        "glamorous bikini with a flowing sheer cover-up",
    ],
}


# ---------------------------------------------------------------------------
# THEMES / STYLE BOOSTS
# ---------------------------------------------------------------------------

SAFETY_SUFFIX = (
    "adult woman, confident swimwear and fashion photography, "
    "tasteful non-explicit presentation, no nudity, "
    "no exposed nipples or genitals, not sexually explicit"
)


GLAM_CHANCE = 0.6

GLAM_BOOST = (
    "striking beauty, radiant natural skin, beautiful facial features, "
    "glamorous styling, confident presence, polished Instagram aesthetic"
)


BODY_BOOST_CHANCE = 0.85

BODY_BOOST = (
    "naturally fuller feminine proportions, "
    "noticeably curvy silhouette, "
    "fuller hips and thighs, "
    "defined waist, "
    "realistic body proportions"
)


def _maybe_glam() -> str:
    if random.random() < GLAM_CHANCE:
        return f" {GLAM_BOOST}."
    return ""


def _maybe_body_boost() -> str:
    if random.random() < BODY_BOOST_CHANCE:
        return f" {BODY_BOOST}."
    return ""


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------

def _pick(lst, seed):
    return lst[seed % len(lst)]


# ---------------------------------------------------------------------------
# PROMPT BUILDING
# ---------------------------------------------------------------------------

def build_prompt(theme: dict, seed: int = 0) -> str:
    """
    Build the main image-generation prompt.

    Character = person / body / appearance
    Outfit    = swimwear / clothing
    Theme     = location / atmosphere
    Camera    = photographic style
    """

    char = _pick(CHARACTERS, seed)

    camera = _pick(
        CAMERA_STYLES,
        seed + 1
    )

    outfit = _pick(
        OUTFITS.get(
            theme["style"],
            ["stylish casual outfit"]
        ),
        seed + 2
    )

    return (
        f"Full-body photograph, wide shot from head to knees, "
        f"her complete figure clearly visible in frame. "
        f"{char}. "
        f"She is wearing {outfit}. "
        f"She is at {theme['setting']}. "
        f"{theme['vibe']} mood. "
        f"Relaxed confident natural pose, standing, whole body in shot. "
        f"{camera}. "
        f"Candid real-life Instagram photo, "
        f"not a professional studio photoshoot, "
        f"authentic social-media photography, "
        f"realistic skin texture, realistic proportions, "
        f"natural lighting and believable environment."
        f"{_maybe_body_boost()}"
        f"{_maybe_glam()} "
        f"{SAFETY_SUFFIX}."
    )


# ---------------------------------------------------------------------------
# MULTI-SHOT PROMPT
# ---------------------------------------------------------------------------

def build_shot_prompt(
    theme: dict,
    shot: int,
    seed: int = 0
) -> str:

    char = _pick(
        CHARACTERS,
        seed
    )

    camera = _pick(
        CAMERA_STYLES,
        seed + shot + 1
    )

    outfit = _pick(
        OUTFITS.get(
            theme["style"],
            ["stylish casual outfit"]
        ),
        seed
    )

    shot_angles = [
        (
            f"full-body shot showing her complete outfit and natural body "
            f"proportions, {theme['setting']}, warm golden-hour light"
        ),

        (
            "casual mirror selfie, phone visible in the reflection, "
            "relaxed confident pose, looking naturally toward the mirror"
        ),

        (
            f"three-quarter body shot, candid moment, looking slightly to "
            f"the side, {theme['setting']}"
        ),

        (
            f"full-body beach lifestyle photograph, walking naturally, "
            f"{theme['setting']}, sunlight and realistic shadows"
        ),

        (
            f"seated resort lifestyle photograph, relaxed posture, "
            f"{theme['setting']}, natural ambient light"
        ),
    ]

    angle = _pick(
        shot_angles,
        shot
    )

    return (
        f"{char}. "
        f"She is wearing {outfit}. "
        f"{angle}. "
        f"{theme['vibe'].capitalize()} expression. "
        f"{camera}. "
        f"Authentic Instagram lifestyle photography, "
        f"realistic skin texture, natural body proportions, "
        f"realistic lighting, candid composition."
        f"{_maybe_body_boost()}"
        f"{_maybe_glam()} "
        f"{SAFETY_SUFFIX}."
    )


# ---------------------------------------------------------------------------
# POLLINATIONS
# ---------------------------------------------------------------------------

def generate_hf_image(
    prompt: str,
    api_key: str,
    width: int = 768,
    height: int = 1344
) -> bytes | None:

    """
    Generate an image through Pollinations.ai.

    `api_key` is retained for compatibility with the existing call site.
    Authentication is taken from POLLINATIONS_TOKEN when available.
    """

    token = os.environ.get(
        "POLLINATIONS_TOKEN",
        ""
    ).strip() or None

    headers = (
        {"Authorization": f"Bearer {token}"}
        if token
        else {}
    )

    encoded_prompt = urllib.parse.quote(prompt)

    url = (
        f"{POLLINATIONS_BASE}/{encoded_prompt}"
    )

    params = {
        "width": width,
        "height": height,
        "model": "flux",
        "nologo": "true",
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=120
        )

        content_type = r.headers.get(
            "content-type",
            ""
        )

        if (
            r.status_code == 200
            and content_type.startswith("image")
        ):
            return r.content

        print(
            f"  Pollinations: HTTP {r.status_code} — "
            f"{r.text[:200]}"
        )

    except Exception as e:
        print(
            f"  Pollinations error: {e}"
        )

    return None


# ---------------------------------------------------------------------------
# FAL.AI
# ---------------------------------------------------------------------------

FAL_MODEL_URL = (
    "https://fal.run/fal-ai/flux/dev"
)


def generate_fal_image(
    prompt: str,
    width: int = 768,
    height: int = 1344
) -> bytes | None:

    """
    Generate through fal.ai if FAL_API_KEY is configured.
    """

    api_key = os.environ.get(
        "FAL_API_KEY",
        ""
    ).strip()

    if not api_key:
        return None

    try:
        r = requests.post(
            FAL_MODEL_URL,
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "image_size": {
                    "width": width,
                    "height": height
                },
                "num_images": 1,
            },
            timeout=90,
        )

        if r.status_code != 200:
            print(
                f"  fal.ai: HTTP {r.status_code} — "
                f"{r.text[:200]}"
            )
            return None

        images = r.json().get(
            "images",
            []
        )

        if not images:
            print(
                "  fal.ai: no images in response"
            )
            return None

        img_r = requests.get(
            images[0]["url"],
            timeout=60
        )

        if img_r.status_code == 200:
            return img_r.content

        print(
            f"  fal.ai: image download failed: "
            f"{img_r.status_code}"
        )

    except Exception as e:
        print(
            f"  fal.ai error: {e}"
        )

    return None


# ---------------------------------------------------------------------------
# CLOUDFLARE
# ---------------------------------------------------------------------------

CLOUDFLARE_MODEL = (
    "@cf/stabilityai/stable-diffusion-xl-base-1.0"
)

# SDXL supports negative_prompt but we weren't passing one - this is a
# real, direct lever for "looks AI" that the free Pollinations source
# never had available.
CLOUDFLARE_NEGATIVE_PROMPT = (
    "3d render, cgi, digital art, illustration, painting, cartoon, anime, "
    "airbrushed, plastic skin, waxy skin, doll-like, uncanny, artificial, "
    "over-smoothed, symmetrical perfect face, studio backdrop, "
    "close-up crop, headshot only, cropped body, blurry, low quality, "
    "deformed, extra limbs, bad anatomy, watermark, text, logo"
)


def generate_cloudflare_image(
    prompt: str,
    width: int = 768,
    height: int = 1344
) -> bytes | None:

    """
    Generate through Cloudflare Workers AI if credentials exist.
    """

    account_id = os.environ.get(
        "CLOUDFLARE_ACCOUNT_ID",
        ""
    ).strip()

    api_token = os.environ.get(
        "CLOUDFLARE_API_TOKEN",
        ""
    ).strip()

    if not account_id or not api_token:
        return None

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{CLOUDFLARE_MODEL}"
    )

    try:
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}"
            },
            json={
                "prompt": prompt,
                "negative_prompt": CLOUDFLARE_NEGATIVE_PROMPT,
                "width": width,
                "height": height
            },
            timeout=60,
        )

        if r.status_code != 200:
            print(
                f"  Cloudflare: HTTP {r.status_code} — "
                f"{r.text[:200]}"
            )
            return None

        content_type = r.headers.get(
            "content-type",
            ""
        )

        if content_type.startswith("image"):
            return r.content

        try:
            b64 = (
                r.json()
                .get("result", {})
                .get("image")
            )

            if b64:
                return base64.b64decode(b64)

        except Exception:
            pass

        print(
            "  Cloudflare: unexpected response "
            f"(content-type={content_type})"
        )

    except Exception as e:
        print(
            f"  Cloudflare error: {e}"
        )

    return None


# ---------------------------------------------------------------------------
# GEMINI
# ---------------------------------------------------------------------------

GEMINI_MODEL = (
    "gemini-3.1-flash-image"
)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/"
    f"v1/models/{GEMINI_MODEL}:generateContent"
)


def generate_gemini_image(
    prompt: str
) -> bytes | None:

    """
    Generate through Gemini when GEMINI_API_KEY is configured.
    """

    api_key = os.environ.get(
        "GEMINI_API_KEY",
        ""
    ).strip()

    if not api_key:
        return None

    try:
        r = requests.post(
            GEMINI_URL,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            timeout=60,
        )

        if r.status_code != 200:
            print(
                f"  Gemini: HTTP {r.status_code} — "
                f"{r.text[:200]}"
            )
            return None

        parts = (
            r.json()
            .get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )

        for part in parts:
            inline = part.get(
                "inlineData"
            )

            if inline and inline.get("data"):
                return base64.b64decode(
                    inline["data"]
                )

        refusal = " ".join(
            p.get("text", "")
            for p in parts
            if "text" in p
        )

        print(
            "  Gemini returned no image: "
            f"{refusal[:200]}"
        )

    except Exception as e:
        print(
            f"  Gemini error: {e}"
        )

    return None


# ---------------------------------------------------------------------------
# PROVIDER FALLBACK
# ---------------------------------------------------------------------------

def generate_image_bytes(
    prompt: str,
    hf_api_key: str
) -> tuple[bytes, str] | tuple[None, None]:

    """
    Try the configured image providers in order.
    """

    fal_bytes = generate_fal_image(
        prompt
    )

    if fal_bytes:
        return fal_bytes, "fal"

    cf_bytes = generate_cloudflare_image(
        prompt
    )

    if cf_bytes:
        return cf_bytes, "cloudflare"

    gemini_bytes = generate_gemini_image(
        prompt
    )

    if gemini_bytes:
        return gemini_bytes, "gemini"

    pollinations_bytes = generate_hf_image(
        prompt,
        hf_api_key
    )

    if pollinations_bytes:
        return pollinations_bytes, "pollinations"

    return None, None


# ---------------------------------------------------------------------------
# IMGBB UPLOAD
# ---------------------------------------------------------------------------

def upload_to_imgbb(
    image_bytes: bytes,
    api_key: str
) -> str | None:

    try:
        b64 = base64.b64encode(
            image_bytes
        ).decode()

        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": api_key,
                "image": b64
            },
            timeout=30,
        )

        if r.status_code == 200:
            return r.json()["data"]["url"]

        print(
            f"  ImgBB upload failed: "
            f"{r.status_code}"
        )

    except Exception as e:
        print(
            f"  ImgBB error: {e}"
        )

    return None


# ---------------------------------------------------------------------------
# IMAGE POST-PROCESSING
# ---------------------------------------------------------------------------

def process_image(
    image_bytes: bytes,
    target_width: int = TARGET_WIDTH,
    add_grain: bool = True,
    overlay_text: str | None = None
) -> bytes:

    """
    Upscale and optionally apply subtle photographic processing.

    This does NOT change the generated person's body or clothing.
    It only changes the final pixels.
    """

    try:
        im = Image.open(
            io.BytesIO(image_bytes)
        ).convert("RGB")

        # Upscale if provider returned a smaller image.
        if im.width < target_width:

            scale = (
                target_width / im.width
            )

            im = im.resize(
                (
                    target_width,
                    round(im.height * scale)
                ),
                Image.LANCZOS
            )

        if add_grain:

            arr = np.array(
                im
            ).astype(np.float32)

            noise = np.random.normal(
                0,
                6.5,
                arr.shape[:2]
            )[:, :, None]

            im = Image.fromarray(
                np.clip(
                    arr + noise,
                    0,
                    255
                ).astype(np.uint8)
            )

            im = im.filter(
                ImageFilter.GaussianBlur(
                    radius=0.6
                )
            )

            im = im.filter(
                ImageFilter.UnsharpMask(
                    radius=2,
                    percent=80,
                    threshold=2
                )
            )

            im = ImageEnhance.Color(
                im
            ).enhance(0.92)

            im = ImageEnhance.Contrast(
                im
            ).enhance(0.97)

        if overlay_text:
            im = add_overlay_text(im, overlay_text)

        out = io.BytesIO()

        im.save(
            out,
            format="JPEG",
            quality=92
        )

        return out.getvalue()

    except Exception as e:

        print(
            f"  Image processing error "
            f"(using original): {e}"
        )

        return image_bytes


# ---------------------------------------------------------------------------
# MAIN GENERATION FUNCTION
# ---------------------------------------------------------------------------

def generate_image(
    theme: dict,
    hf_api_key: str,
    imgbb_api_key: str,
    seed: int = 0,
    overlay_text: str | None = None
) -> str | None:

    prompt = build_prompt(
        theme,
        seed
    )

    print(
        f"  Prompt: {prompt[:250]}..."
    )

    image_bytes, source = (
        generate_image_bytes(
            prompt,
            hf_api_key
        )
    )

    if not image_bytes:
        print(
            "  No image provider succeeded."
        )
        return None

    print(
        f"  Source: {source}"
    )

    if overlay_text:
        print(f"  Overlay: {overlay_text}")

    # Pollinations tends to benefit from grain.
    # Higher-quality providers can skip it.
    image_bytes = process_image(
        image_bytes,
        add_grain=(
            source == "pollinations"
        ),
        overlay_text=overlay_text
    )

    print(
        "  Uploading to ImgBB..."
    )

    return upload_to_imgbb(
        image_bytes,
        imgbb_api_key
    )

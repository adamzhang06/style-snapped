"""
Downloads 5 high-quality fashion images per category for both models
using DuckDuckGo image search (no API key required).

Output:
  backend/demo_images/1_my_vibe_model/<Category>/  (replaced with HQ images)
  backend/demo_images/2_my_vibe_model/<Category>/  (replaced with HQ images)
"""

import time
import json
import random
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from ddgs import DDGS

SCRIPT_DIR   = Path(__file__).parent
BACKEND_DIR  = SCRIPT_DIR.parent
DEMO_ROOT    = BACKEND_DIR / "demo_images"
IMAGES_PER_CLASS = 5
MIN_DIMENSION = 400   # skip images smaller than this

# Search queries tuned per category — "fashion editorial" gets cleaner shots
SEARCH_QUERIES = {
    # Model 1
    "Athleisure":             "athleisure outfit fashion woman studio white background",
    "Boho / Cottagecore":     "bohemian cottagecore fashion outfit editorial",
    "Business Casual":        "business casual outfit woman editorial white background",
    "Business Formal":        "business formal suit woman professional editorial",
    "Casual Basics":          "casual basics outfit fashion minimal white background",
    "Edgy / Alternative":     "edgy alternative fashion outfit editorial dark",
    "Loungewear / Sleepwear": "loungewear cozy outfit fashion editorial",
    "Streetwear":             "streetwear outfit fashion editorial urban",
    "Traditional / Ethnic Wear": "traditional ethnic wear fashion editorial colorful",
    # Model 2
    "Boho Chic":              "boho chic fashion outfit editorial",
    "Smart Casual / Office":  "smart casual office outfit woman editorial",
}


def safe_folder_name(name: str) -> str:
    return name.replace("/", "-").replace(" ", "_")


def fetch_images(query: str, n: int = IMAGES_PER_CLASS) -> list[str]:
    """Return up to n image URLs for a query, with retry on rate limit."""
    for attempt in range(4):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=n * 4,
                    size="Large",
                    type_image="photo",
                ))
            urls = [r["image"] for r in results if r.get("image")]
            random.shuffle(urls)
            return urls
        except Exception as e:
            wait = 8 * (attempt + 1)
            print(f"    rate limited, retrying in {wait}s... ({e})")
            time.sleep(wait)
    return []


def download_image(url: str, dest: Path) -> bool:
    """Download one image; return True on success."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="JPEG", quality=92)
        return True
    except Exception:
        return False


def populate_category(model_folder: str, category: str):
    query = SEARCH_QUERIES.get(category, f"{category} fashion outfit editorial")
    safe  = safe_folder_name(category)
    dest_dir = DEMO_ROOT / model_folder / safe

    # Skip if already fully populated
    if dest_dir.exists() and len(list(dest_dir.glob("*.jpg"))) >= IMAGES_PER_CLASS:
        print(f"  [{model_folder}] {category} — already done, skipping")
        return

    # Clear partial existing images
    if dest_dir.exists():
        for f in dest_dir.glob("*.jpg"):
            f.unlink()

    print(f"  [{model_folder}] {category}")
    print(f"    query: \"{query}\"")

    urls = fetch_images(query)
    saved = 0
    for i, url in enumerate(urls):
        if saved >= IMAGES_PER_CLASS:
            break
        dest = dest_dir / f"{saved + 1:02d}.jpg"
        if download_image(url, dest):
            saved += 1
            print(f"    ✓ {saved}/{IMAGES_PER_CLASS}")
        else:
            pass  # silently skip bad URLs

    if saved < IMAGES_PER_CLASS:
        print(f"    ⚠ only got {saved}/{IMAGES_PER_CLASS} images")

    time.sleep(4)     # be polite between searches to avoid rate limits


# ---------------------------------------------------------------------------
M1_CLASSES = [
    "Athleisure", "Boho / Cottagecore", "Business Casual", "Business Formal",
    "Casual Basics", "Edgy / Alternative", "Loungewear / Sleepwear",
    "Streetwear", "Traditional / Ethnic Wear",
]

M2_CLASSES = [
    "Athleisure", "Boho Chic", "Casual Basics",
    "Smart Casual / Office", "Streetwear", "Traditional / Ethnic Wear",
]

print("=== Fetching HQ demo images ===\n")

print("--- Model 1 (1_my_vibe_model) ---")
for cls in M1_CLASSES:
    populate_category("1_my_vibe_model", cls)

print("\n--- Model 2 (2_my_vibe_model) ---")
for cls in M2_CLASSES:
    populate_category("2_my_vibe_model", cls)

print("\nDone. Images saved to", DEMO_ROOT)

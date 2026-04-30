"""
Fetches 5 additional demo images (06-10) per category for model 3.
Uses distinct queries from both the training data fetch (1_fetch_training_images.py)
and the original demo fetch (fetch_demo_images_hq.py) to avoid overlap.

Output: backend/demo_images/3_my_vibe_model/<Category>/06.jpg ... 10.jpg
"""

import time
import random
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from ddgs import DDGS

SCRIPT_DIR   = Path(__file__).parent
BACKEND_DIR  = SCRIPT_DIR.parent
DEMO_ROOT    = BACKEND_DIR / "demo_images" / "3_my_vibe_model"
IMAGES_TO_ADD = 5
MIN_DIMENSION = 400
START_INDEX   = 6   # existing images are 01-05

# Queries intentionally distinct from training queries and original demo queries
EXTRA_QUERIES = {
    "Athleisure": "sporty chic woman activewear lifestyle photo",
    "Boho_-_Cottagecore": "boho maxi dress floral meadow woman photo",
    "Business_Casual": "woman blazer trousers office chic lookbook photo",
    "Business_Formal": "tailored suit woman boardroom executive photo",
    "Casual_Basics": "woman white tee jeans sneakers minimal street photo",
    "Edgy_-_Alternative": "punk rock woman leather jacket studs festival photo",
    "Loungewear_-_Sleepwear": "woman knit set cozy indoor fashion photo",
    "Streetwear": "sneakerhead outfit woman cargo pants hoodie city photo",
    "Traditional_-_Ethnic_Wear": "saree sari kimono hanbok woman fashion portrait photo",
}


def fetch_images(query: str, n: int = IMAGES_TO_ADD * 5) -> list[str]:
    for attempt in range(4):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=n,
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


print("=== Fetching 5 additional demo images per category (model 3) ===\n")

for safe_name, query in EXTRA_QUERIES.items():
    dest_dir = DEMO_ROOT / safe_name
    existing = sorted(dest_dir.glob("*.jpg")) if dest_dir.exists() else []
    target_end = START_INDEX + IMAGES_TO_ADD - 1  # 06..10

    # Count how many extra images already exist (index >= START_INDEX)
    already_extra = [f for f in existing if int(f.stem) >= START_INDEX]
    if len(already_extra) >= IMAGES_TO_ADD:
        print(f"  {safe_name} — already has {len(already_extra)} extra images, skipping")
        continue

    next_idx = START_INDEX + len(already_extra)
    needed   = IMAGES_TO_ADD - len(already_extra)

    print(f"  {safe_name}")
    print(f"    query: \"{query}\"")

    urls  = fetch_images(query)
    saved = 0
    for url in urls:
        if saved >= needed:
            break
        dest = dest_dir / f"{next_idx:02d}.jpg"
        if download_image(url, dest):
            saved    += 1
            next_idx += 1
            print(f"    ✓ {START_INDEX + len(already_extra) - 1 + saved}/{target_end}")

    if saved < needed:
        print(f"    ⚠ only got {saved}/{needed} extra images")

    time.sleep(4)

print("\nDone.")
print(f"Images saved to: {DEMO_ROOT}")

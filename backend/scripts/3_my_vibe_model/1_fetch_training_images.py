"""
Script 1: Scrape ~200 high-quality fashion images per category from the web
using DuckDuckGo Image Search (no API key required).

Outputs (backend/3_my_vibe_model/training_data/<Category>/):
  01.jpg, 02.jpg, ...  up to TARGET_PER_CLASS images per category

Resumable: already-downloaded images are counted, only the gap is filled.
"""

import time
import random
import hashlib
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from ddgs import DDGS

SCRIPT_DIR    = Path(__file__).parent
BACKEND_DIR   = SCRIPT_DIR.parent.parent
OUTPUT_ROOT   = BACKEND_DIR / "3_my_vibe_model" / "training_data"

TARGET_PER_CLASS = 200
MIN_DIMENSION    = 350    # skip tiny images
REQUEST_TIMEOUT  = 10
DELAY_BETWEEN_QUERIES  = 6   # seconds — DDG rate limit is aggressive
DELAY_BETWEEN_IMAGES   = 0.3

# ---------------------------------------------------------------------------
# Multiple diverse queries per class — variety reduces query-specific bias
# ---------------------------------------------------------------------------
QUERIES: dict[str, list[str]] = {
    "Athleisure": [
        "athleisure outfit woman street style",
        "sporty casual fashion editorial white background",
        "athletic wear fashion lookbook",
        "yoga leggings outfit street fashion",
        "gym to street fashion outfit woman",
        "performance wear fashion editorial",
    ],
    "Boho / Cottagecore": [
        "bohemian fashion outfit editorial",
        "cottagecore aesthetic fashion lookbook",
        "boho chic style outfit woman",
        "flowy bohemian dress fashion editorial",
        "vintage boho fashion lookbook",
        "cottagecore outfit nature fashion",
    ],
    "Business Casual": [
        "business casual outfit woman editorial",
        "smart casual office look fashion",
        "professional casual outfit woman",
        "work outfit woman fashion editorial",
        "business casual blazer outfit",
        "polished casual fashion editorial",
    ],
    "Business Formal": [
        "business formal suit woman editorial",
        "power suit fashion editorial",
        "formal office outfit woman",
        "corporate fashion editorial woman",
        "blazer formal outfit editorial",
        "professional formal fashion lookbook",
    ],
    "Casual Basics": [
        "casual basics fashion outfit",
        "minimalist everyday fashion editorial",
        "simple casual outfit editorial",
        "casual chic basics fashion",
        "relaxed casual fashion lookbook",
        "everyday basics fashion woman",
    ],
    "Edgy / Alternative": [
        "edgy fashion outfit editorial",
        "alternative fashion style lookbook",
        "punk fashion outfit editorial",
        "dark fashion editorial woman",
        "gothic fashion lookbook",
        "grunge fashion outfit editorial",
    ],
    "Loungewear / Sleepwear": [
        "loungewear fashion editorial",
        "cozy home outfit fashion editorial",
        "sleepwear fashion lookbook",
        "comfortable loungewear outfit",
        "pajama set fashion editorial",
        "soft loungewear fashion woman",
    ],
    "Streetwear": [
        "streetwear fashion editorial",
        "urban street style outfit lookbook",
        "streetwear lookbook fashion",
        "hypebeast fashion outfit",
        "oversized streetwear fashion editorial",
        "street fashion urban youth",
    ],
    "Traditional / Ethnic Wear": [
        "traditional ethnic fashion editorial",
        "cultural fashion outfit editorial",
        "ethnic wear fashion lookbook",
        "folk traditional fashion editorial",
        "cultural dress fashion lookbook",
        "ethnic embroidered fashion outfit",
    ],
}


def fetch_urls(query: str, n: int = 60) -> list[str]:
    """Return up to n image URLs, retrying on rate limit."""
    for attempt in range(5):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=n,
                    size="Large",
                    type_image="photo",
                ))
            return [r["image"] for r in results if r.get("image")]
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"      rate limit, retrying in {wait}s ({e})")
            time.sleep(wait)
    return []


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


def download_image(url: str, dest: Path) -> bool:
    try:
        resp = requests.get(
            url, timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="JPEG", quality=92)
        return True
    except Exception:
        return False


def populate_class(category: str, queries: list[str]):
    safe     = category.replace("/", "-").replace(" ", "_")
    dest_dir = OUTPUT_ROOT / safe
    dest_dir.mkdir(parents=True, exist_ok=True)

    existing  = sorted(dest_dir.glob("*.jpg"))
    saved     = len(existing)
    next_idx  = saved + 1
    seen_urls: set[str] = set()

    print(f"\n  {category}  ({saved} already saved, target {TARGET_PER_CLASS})")

    if saved >= TARGET_PER_CLASS:
        print(f"    already complete — skipping")
        return

    for query in queries:
        if saved >= TARGET_PER_CLASS:
            break

        print(f"    query: \"{query}\"")
        urls = fetch_urls(query)
        random.shuffle(urls)

        for url in urls:
            if saved >= TARGET_PER_CLASS:
                break
            if url in seen_urls:
                continue
            seen_urls.add(url)

            dest = dest_dir / f"{next_idx:03d}.jpg"
            if download_image(url, dest):
                saved    += 1
                next_idx += 1
                if saved % 20 == 0 or saved == TARGET_PER_CLASS:
                    print(f"    ✓ {saved}/{TARGET_PER_CLASS}")
            time.sleep(DELAY_BETWEEN_IMAGES)

        time.sleep(DELAY_BETWEEN_QUERIES)

    if saved < TARGET_PER_CLASS:
        print(f"    ⚠ finished with {saved}/{TARGET_PER_CLASS} — DDG ran dry")
    else:
        print(f"    ✓ complete ({saved} images)")


# ---------------------------------------------------------------------------
print("=== Fetching training images (Model 3) ===")
print(f"Target: {TARGET_PER_CLASS} images × {len(QUERIES)} classes = "
      f"{TARGET_PER_CLASS * len(QUERIES)} total")
print(f"Output: {OUTPUT_ROOT}\n")

for cat, qs in QUERIES.items():
    populate_class(cat, qs)

# Summary
print("\n=== Summary ===")
total = 0
for cat in QUERIES:
    safe = cat.replace("/", "-").replace(" ", "_")
    n = len(list((OUTPUT_ROOT / safe).glob("*.jpg")))
    total += n
    status = "✓" if n >= TARGET_PER_CLASS else f"⚠ {n}"
    print(f"  {cat:<30} {status}")
print(f"\n  Total: {total} images")
print("\nNext step: run  2_train.py")

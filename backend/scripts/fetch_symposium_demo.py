"""
Fetch 15 symposium demo images for model 3.

Scrapes fresh images with queries that differ from training, runs each through
model.pt, and selects the 15 highest-confidence results spread across classes.

Output: backend/demo_images/3_my_vibe_model/Symposium_Demo/
        Files named:  01_Athleisure.jpg, 02_Streetwear.jpg, ...
"""

import io
import json
import time
import random
import requests
import torch
import torch.nn as nn
from pathlib import Path
from PIL import Image
from torchvision import models, transforms
from ddgs import DDGS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
BACKEND_DIR  = SCRIPT_DIR.parent
MODEL_DIR    = BACKEND_DIR / "3_my_vibe_model"
OUTPUT_DIR   = BACKEND_DIR / "demo_images" / "3_my_vibe_model" / "Symposium_Demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES_DIR = BACKEND_DIR / "demo_images" / "3_my_vibe_model" / "_symposium_candidates"
CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

TARGET_FINAL     = 15
CANDIDATES_PER_Q = 6   # images to attempt per query
REQUEST_TIMEOUT  = 10
MIN_DIM          = 300

# ---------------------------------------------------------------------------
# Queries — intentionally different from training queries to get fresh images
# ---------------------------------------------------------------------------
QUERIES: dict[str, list[str]] = {
    "Athleisure": [
        "athleisure street style 2024 full outfit",
        "sporty chic outfit running errands",
    ],
    "Boho / Cottagecore": [
        "cottagecore dress outdoor photoshoot",
        "boho festival look summer 2024",
    ],
    "Business Casual": [
        "smart casual office outfit inspiration 2024",
        "business casual work look blazer trousers",
    ],
    "Business Formal": [
        "power suit fashion editorial 2024",
        "formal workwear executive style",
    ],
    "Casual Basics": [
        "minimalist everyday basics outfit jeans tee",
        "simple casual outfit white shirt neutral tones",
    ],
    "Edgy / Alternative": [
        "alternative punk grunge fashion street style",
        "dark aesthetic edgy outfit 2024",
    ],
    "Loungewear / Sleepwear": [
        "cozy loungewear set matching outfit at home",
        "chic loungewear aesthetic 2024",
    ],
    "Streetwear": [
        "streetwear hype outfit sneakers 2024",
        "urban street fashion oversized hoodie",
    ],
    "Traditional / Ethnic Wear": [
        "traditional cultural fashion editorial",
        "ethnic wear modern styling 2024",
    ],
}

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
with open(MODEL_DIR / "classes.json") as f:
    _raw = json.load(f)
CLASSES = [_raw[k] for k in sorted(_raw, key=lambda x: int(x))]
NUM_CLASSES = len(CLASSES)

resnet = models.resnet50(weights=None)
resnet.fc = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(resnet.fc.in_features, NUM_CLASSES),
)
resnet.load_state_dict(torch.load(MODEL_DIR / "model.pt", map_location="cpu"))
resnet.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def score_image(img: Image.Image) -> tuple[str, float]:
    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(resnet(tensor), dim=-1)[0]
    idx = int(probs.argmax())
    return CLASSES[idx], round(float(probs[idx]) * 100, 1)

# ---------------------------------------------------------------------------
# Scrape candidates
# ---------------------------------------------------------------------------
print("Scraping candidate images …")
ddgs = DDGS()

# Each entry: {"path": Path, "predicted_class": str, "expected_class": str, "confidence": float}
candidates: list[dict] = []

for class_name, queries in QUERIES.items():
    for query in queries:
        print(f"  [{class_name}] {query}")
        try:
            results = list(ddgs.images(query, max_results=12))
        except Exception as e:
            print(f"    DDG error: {e}")
            time.sleep(8)
            continue

        fetched = 0
        for r in results:
            if fetched >= CANDIDATES_PER_Q:
                break
            url = r.get("image", "")
            if not url:
                continue
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                                    headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                if min(img.size) < MIN_DIM:
                    continue

                safe_class = class_name.replace(" / ", "_").replace(" ", "_")
                fname = CANDIDATES_DIR / f"{safe_class}_{len(candidates):04d}.jpg"
                img.save(fname, "JPEG", quality=90)

                pred_class, conf = score_image(img)
                candidates.append({
                    "path": fname,
                    "expected_class": class_name,
                    "predicted_class": pred_class,
                    "confidence": conf,
                })
                print(f"    ✓ saved  pred={pred_class} ({conf}%)")
                fetched += 1
            except Exception as e:
                print(f"    ✗ {e}")
            time.sleep(0.4)

        time.sleep(5)

# ---------------------------------------------------------------------------
# Select 15 best: prefer images where model is confident AND correct,
# ensure spread across classes (up to 2 per class to fill 15).
# ---------------------------------------------------------------------------
print(f"\nScored {len(candidates)} candidates — selecting best {TARGET_FINAL} …")

# Sort by confidence descending
candidates.sort(key=lambda c: c["confidence"], reverse=True)

# First pass: correct predictions only
selected: list[dict] = []
per_class: dict[str, int] = {}
MAX_PER_CLASS = 2

for c in candidates:
    if len(selected) >= TARGET_FINAL:
        break
    if c["predicted_class"] != c["expected_class"]:
        continue
    cls = c["predicted_class"]
    if per_class.get(cls, 0) >= MAX_PER_CLASS:
        continue
    selected.append(c)
    per_class[cls] = per_class.get(cls, 0) + 1

# Second pass: fill remaining slots with highest-confidence images regardless
if len(selected) < TARGET_FINAL:
    selected_paths = {s["path"] for s in selected}
    for c in candidates:
        if len(selected) >= TARGET_FINAL:
            break
        if c["path"] in selected_paths:
            continue
        cls = c["predicted_class"]
        if per_class.get(cls, 0) >= MAX_PER_CLASS + 1:
            continue
        selected.append(c)
        per_class[cls] = per_class.get(cls, 0) + 1

# Sort selected by class name for tidy numbering
selected.sort(key=lambda c: c["predicted_class"])

# ---------------------------------------------------------------------------
# Write final output with descriptive filenames
# ---------------------------------------------------------------------------
print(f"\nWriting {len(selected)} demo images to {OUTPUT_DIR} …\n")
for i, c in enumerate(selected, 1):
    label = c["predicted_class"].replace(" / ", "-").replace(" ", "_")
    out_name = f"{i:02d}_{label}.jpg"
    out_path = OUTPUT_DIR / out_name

    img = Image.open(c["path"]).convert("RGB")
    img.save(out_path, "JPEG", quality=92)
    print(f"  {out_name}  ← pred={c['predicted_class']} ({c['confidence']}%)"
          f"  [expected: {c['expected_class']}]")

print(f"\nDone. {len(selected)} images in {OUTPUT_DIR}")
print("Candidate scratch folder kept at:", CANDIDATES_DIR)

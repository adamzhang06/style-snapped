"""
Saves 5 representative demo images per category for both models.

Model 1 — picks the 5 images per class with the highest label confidence
          (proxy: closest to the class centroid in CSV order, so just the
          first 5 unique samples found for each class).

Model 2 — prioritises centroid images (is_centroid=1, sorted by centroid_rank)
          since those are mathematically the most prototypical members of each
          cluster. Fills up to 5 with the closest non-centroid images
          (lowest dist_to_center within the cluster whose label matches).

Output:
  backend/demo_images/
    1_my_vibe_model/<Category Name>/<image_id>.jpg   (5 per class)
    2_my_vibe_model/<Category Name>/<image_id>.jpg   (5 per class)
"""

import os
import json
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found — add it to backend/scripts/.env")

BACKEND_DIR  = SCRIPT_DIR.parent
DEMO_ROOT    = BACKEND_DIR / "demo_images"
IMAGES_PER_CLASS = 5

# ---------------------------------------------------------------------------
# Load HuggingFace dataset once
# ---------------------------------------------------------------------------
print("Loading HuggingFace dataset (this may take a moment)...")
hf_dataset = load_dataset(
    "ashraq/fashion-product-images-small",
    split="train",
    token=HF_TOKEN,
)
print(f"  Loaded {len(hf_dataset)} images.")

# ---------------------------------------------------------------------------
# Helper: save a PIL image to disk as JPEG
# ---------------------------------------------------------------------------
def save_image(pil_img, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    pil_img.save(dest_path, format="JPEG", quality=92)


# ---------------------------------------------------------------------------
# Helper: build a {image_id: PIL.Image} index for a specific set of ids
# ---------------------------------------------------------------------------
def build_index(needed_ids: set) -> dict:
    index = {}
    for item in hf_dataset:
        if item["id"] in needed_ids:
            index[item["id"]] = item["image"]
        if len(index) == len(needed_ids):
            break
    return index


# ===========================================================================
# MODEL 1
# ===========================================================================
print("\n--- Model 1 (1_my_vibe_model) ---")

m1_dir      = BACKEND_DIR / "1_my_vibe_model"
m1_csv      = m1_dir / "synthetic_aesthetics.csv"
m1_classes_path = m1_dir / "label_classes.json"

with open(m1_classes_path) as f:
    m1_classes = json.load(f)   # list

df1 = pd.read_csv(m1_csv)
df1 = df1[df1["vibe"] != "DROP"].copy()
df1["image_id"] = df1["image_id"].astype(int)

# For each class, take the first N rows (earliest labeled = least ambiguous
# since the Gemini calls are sequential and fresh early in the run)
m1_picks: dict[str, list[int]] = {}
for cls in m1_classes:
    rows = df1[df1["vibe"] == cls]["image_id"].tolist()
    m1_picks[cls] = rows[:IMAGES_PER_CLASS]
    print(f"  {cls:<30} → {len(m1_picks[cls])} images selected")

needed_m1 = {iid for ids in m1_picks.values() for iid in ids}
print(f"  Fetching {len(needed_m1)} images from HuggingFace...")
m1_index = build_index(needed_m1)

saved_m1 = 0
for cls, ids in m1_picks.items():
    safe_name = cls.replace("/", "-").replace(" ", "_")
    for iid in ids:
        img = m1_index.get(iid)
        if img is None:
            print(f"  WARNING: image {iid} not found, skipping.")
            continue
        dest = DEMO_ROOT / "1_my_vibe_model" / safe_name / f"{iid}.jpg"
        save_image(img, dest)
        saved_m1 += 1

print(f"  Saved {saved_m1} images → {DEMO_ROOT / '1_my_vibe_model'}")


# ===========================================================================
# MODEL 2 — inference-based selection on the 300 centroid images
# synthetic_aesthetics_v3.csv doesn't exist yet (pipeline mid-run), so we
# load the trained model and run inference on the 300 centroid images from
# cluster_assignments.csv, then pick the 5 highest-confidence per class.
# ===========================================================================
print("\n--- Model 2 (2_my_vibe_model) ---")

import torch
import torch.nn as nn
from torchvision import models, transforms

m2_dir          = BACKEND_DIR / "2_my_vibe_model"
m2_classes_path = m2_dir / "classes.json"
m2_model_path   = m2_dir / "model_v3.pt"
m2_assignments  = m2_dir / "cluster_assignments.csv"

with open(m2_classes_path) as f:
    _raw = json.load(f)
m2_classes = [_raw[k] for k in sorted(_raw, key=lambda x: int(x))]
num_classes_m2 = len(m2_classes)

# Load model
print(f"  Loading model_v3.pt ({num_classes_m2} classes)...")
_m2 = models.resnet50(weights=None)
_m2.fc = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(_m2.fc.in_features, num_classes_m2),
)
_m2.load_state_dict(torch.load(m2_model_path, map_location="cpu"))
_m2.eval()

infer_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Load the 300 centroid images (the most prototypical images per cluster)
df_assign = pd.read_csv(m2_assignments)
df_assign["image_id"] = df_assign["image_id"].astype(int)
centroid_ids = df_assign[df_assign["is_centroid"] == 1]["image_id"].tolist()

print(f"  Fetching {len(centroid_ids)} centroid images from HuggingFace...")
m2_index = build_index(set(centroid_ids))

# Run inference on all 300 centroid images, collect (image_id, class, confidence)
print("  Running inference on centroid images...")
results = []
with torch.no_grad():
    for iid in centroid_ids:
        img = m2_index.get(iid)
        if img is None:
            continue
        if img.mode != "RGB":
            img = img.convert("RGB")
        tensor = infer_transform(img).unsqueeze(0)
        logits = _m2(tensor)
        probs  = torch.softmax(logits, dim=-1)[0]
        top_prob, top_idx = probs.max(dim=0)
        results.append({
            "image_id":   iid,
            "class_idx":  top_idx.item(),
            "class_name": m2_classes[top_idx.item()],
            "confidence": top_prob.item(),
        })

df_results = pd.DataFrame(results)

# Pick top 5 highest-confidence images per class
m2_picks: dict[str, list[int]] = {}
for cls in m2_classes:
    sub  = df_results[df_results["class_name"] == cls].sort_values(
        "confidence", ascending=False
    )
    picks = sub["image_id"].head(IMAGES_PER_CLASS).tolist()
    m2_picks[cls] = picks
    top_conf = sub["confidence"].head(IMAGES_PER_CLASS).tolist()
    conf_str = ", ".join(f"{c*100:.0f}%" for c in top_conf)
    print(f"  {cls:<30} → {len(picks)} images  (confidences: {conf_str})")

saved_m2 = 0
for cls, ids in m2_picks.items():
    safe_name = cls.replace("/", "-").replace(" ", "_")
    for iid in ids:
        img = m2_index.get(iid)
        if img is None:
            continue
        dest = DEMO_ROOT / "2_my_vibe_model" / safe_name / f"{iid}.jpg"
        save_image(img, dest)
        saved_m2 += 1

print(f"  Saved {saved_m2} images → {DEMO_ROOT / '2_my_vibe_model'}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\nDone.")
print(f"  Model 1: {saved_m1} images across {len(m1_classes)} categories")
print(f"  Model 2: {saved_m2} images across {len(m2_classes)} categories")
print(f"  All saved under: {DEMO_ROOT}")

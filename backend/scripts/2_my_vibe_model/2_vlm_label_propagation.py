"""
Script 2: Send the 150 centroid images to Gemini, do majority-vote label
resolution per cluster, and propagate the winning label to all 5,000 images.

Reads:   backend/my_vibe_model_3/cluster_assignments.csv
Writes:  backend/my_vibe_model_3/centroid_labels.csv   (150-row audit log)
         backend/my_vibe_model_3/synthetic_aesthetics_v3.csv (final 5k labels)
"""

import os
import time
from collections import Counter

import pandas as pd
from datasets import load_dataset
from google import genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH   = os.path.join(SCRIPT_DIR, "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_TOKEN       = os.getenv("HF_TOKEN")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found — add it to backend/scripts/.env")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found — add it to backend/scripts/.env")

MODEL      = "gemini-3.1-flash-lite-preview"
OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "2_my_vibe_model"))

ASSIGNMENTS_PATH    = os.path.join(OUTPUT_DIR, "cluster_assignments.csv")
CENTROID_LABELS_PATH = os.path.join(OUTPUT_DIR, "centroid_labels.csv")
FINAL_CSV_PATH      = os.path.join(OUTPUT_DIR, "synthetic_aesthetics_v3.csv")

CATEGORIES = [
    "Streetwear",
    "Techwear / Gorpcore",
    "Y2K",
    "Old Money / Quiet Luxury",
    "Cottagecore",
    "Athleisure",
    "Grunge",
    "Boho Chic",
    "Casual Basics",
    "Smart Casual / Office",
    "Traditional / Ethnic Wear",
    "Loungewear / Sleepwear",
]
VALID_OUTPUTS = set(CATEGORIES) | {"DROP"}

PROMPT = f"""You are an expert fashion stylist classifying e-commerce clothing items.

STEP 1 — THE FILTER (CRITICAL)
Look at the item. Is it a watch, wallet, belt, basic underwear/socks, standard footwear, a handbag, or a plain generic accessory with no wearable clothing component?
If YES → output EXACTLY the single word: DROP

STEP 2 — CLASSIFICATION
If the item is a wearable garment, classify it into the single BEST matching category:

{chr(10).join(f'- {c}' for c in CATEGORIES)}

DEFINITIONS:
- Streetwear: Graphic tees, hoodies with bold prints, urban/skate culture, recognizable street brand logos.
- Techwear / Gorpcore: Utility-focused technical fabrics, weather-resistant gear, cargo pockets, outdoor/functional aesthetic.
- Y2K: Low-rise, metallic fabrics, butterfly prints, rhinestones, early-2000s pop-culture references.
- Old Money / Quiet Luxury: Understated neutrals, high-quality fabrics, minimal branding, preppy or heritage tailoring.
- Cottagecore: Flowy floral prints, linen, lace, puff sleeves, pastoral/romantic aesthetic.
- Athleisure: Gym and sports wear worn casually — leggings, track pants, sports brand logos (Nike, Adidas, Puma).
- Grunge: Distressed denim, plaid flannels, dark washed tones, band tees, ripped detailing.
- Boho Chic: Layered jewellery, fringe, ethnic-inspired prints, earthy tones, relaxed silhouettes.
- Casual Basics: Plain t-shirts, standard jeans, simple hoodies — neutral wardrobe staples with no strong style signal.
- Smart Casual / Office: Button-downs, chinos, blazers, loafers — professional but not strictly formal.
- Traditional / Ethnic Wear: Kurtas, sarees, sherwanis, hanboks, or any garment clearly tied to a cultural/traditional origin.
- Loungewear / Sleepwear: Pajamas, robes, sweatpants explicitly for home wear, highly relaxed house clothing.

Output ONLY the exact category name or the word DROP. No punctuation, markdown, or explanation."""

# ---------------------------------------------------------------------------
# Step 1 — Load centroid image IDs
# ---------------------------------------------------------------------------
print("[1/5] Loading cluster assignments...")
df_all = pd.read_csv(ASSIGNMENTS_PATH)
df_centroids = df_all[df_all["is_centroid"] == 1].copy()
print(f"      {len(df_centroids)} centroid rows across "
      f"{df_centroids['cluster_id'].nunique()} clusters.")

# ---------------------------------------------------------------------------
# Step 2 — Load HuggingFace images and build id→image index (centroids only)
# ---------------------------------------------------------------------------
print("[2/5] Loading HuggingFace dataset...")
hf_dataset = load_dataset(
    "ashraq/fashion-product-images-small",
    split="train",
    token=HF_TOKEN,
)
centroid_ids = set(df_centroids["image_id"].astype(int).tolist())
print(f"      Building image index for {len(centroid_ids)} centroid images...")
image_index = {}
for item in hf_dataset:
    if item["id"] in centroid_ids:
        image_index[item["id"]] = item["image"]
    if len(image_index) == len(centroid_ids):
        break
print(f"      Indexed {len(image_index)} centroid images.")

# ---------------------------------------------------------------------------
# Step 3 — VLM labelling (with resume and retry)
# ---------------------------------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

# Resume support: load any previously saved centroid labels
existing_labels: dict[int, str] = {}
if os.path.exists(CENTROID_LABELS_PATH):
    df_existing = pd.read_csv(CENTROID_LABELS_PATH)
    existing_labels = dict(zip(
        df_existing["image_id"].astype(int),
        df_existing["vibe"],
    ))
    print(f"[3/5] Resuming — {len(existing_labels)} centroid labels already saved.")
else:
    print("[3/5] Sending centroid images to Gemini...")

centroid_records = []
rows = df_centroids.sort_values(["cluster_id", "centroid_rank"]).reset_index(drop=True)
total = len(rows)

for i, row in rows.iterrows():
    image_id   = int(row["image_id"])
    cluster_id = int(row["cluster_id"])
    rank       = int(row["centroid_rank"])

    # Resume: skip already-labelled
    if image_id in existing_labels:
        centroid_records.append({
            "image_id":   image_id,
            "cluster_id": cluster_id,
            "centroid_rank": rank,
            "vibe": existing_labels[image_id],
        })
        continue

    image = image_index.get(image_id)
    if image is None:
        print(f"  WARNING: image {image_id} not found in index, skipping.")
        continue

    if image.mode != "RGB":
        image = image.convert("RGB")

    vibe    = None
    retries = 0
    while vibe is None and retries < 5:
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[image, PROMPT],
            )
            raw = response.text.strip()
            if raw in VALID_OUTPUTS:
                vibe = raw
            else:
                # Fuzzy match: find the category whose name is a substring of reply
                matched = [c for c in VALID_OUTPUTS if c.lower() in raw.lower()]
                vibe = matched[0] if matched else "Casual Basics"
                print(f"  NOTE: cluster {cluster_id} rank {rank} fuzzy-matched "
                      f"'{raw}' → '{vibe}'")
        except Exception as e:
            err = str(e)
            if any(code in err for code in ("503", "500", "429", "RESOURCE_EXHAUSTED")):
                retries += 1
                wait = 10 * (2 ** retries)   # 20s, 40s, 80s, 160s, 320s
                print(f"  API error (cluster {cluster_id}, rank {rank}): "
                      f"{err[:80]}. Retry {retries}/5 — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Fatal error at cluster {cluster_id}: {e}")
                vibe = "Casual Basics"

    if vibe is None:
        vibe = "Casual Basics"
        print(f"  Max retries hit for cluster {cluster_id} rank {rank} — "
              f"defaulting to '{vibe}'.")

    centroid_records.append({
        "image_id":      image_id,
        "cluster_id":    cluster_id,
        "centroid_rank": rank,
        "vibe":          vibe,
    })
    existing_labels[image_id] = vibe

    n_done = len(centroid_records)
    print(f"  [{n_done}/{total}] cluster={cluster_id} rank={rank} "
          f"image={image_id} → {vibe}")

    # Checkpoint every 10 labels
    if n_done % 10 == 0:
        pd.DataFrame(centroid_records).to_csv(CENTROID_LABELS_PATH, index=False)

    time.sleep(0.6)   # stay under free-tier rate limits

df_centroid_labels = pd.DataFrame(centroid_records)
df_centroid_labels.to_csv(CENTROID_LABELS_PATH, index=False)
print(f"\n[3/5] All {len(df_centroid_labels)} centroid labels saved → {CENTROID_LABELS_PATH}")

# ---------------------------------------------------------------------------
# Step 4 — Majority-vote label resolution per cluster
# ---------------------------------------------------------------------------
print("[4/5] Resolving cluster labels via majority vote...")
cluster_vibes: dict[int, str] = {}

for cluster_id, grp in df_centroid_labels.groupby("cluster_id"):
    votes = grp["vibe"].tolist()
    counter = Counter(votes)
    top_count = counter.most_common(1)[0][1]
    winners   = [v for v, c in counter.items() if c == top_count]

    if len(winners) == 1:
        # Clear majority (or 2-1 split)
        cluster_vibes[cluster_id] = winners[0]
        print(f"  Cluster {cluster_id:2d}: {counter} → {winners[0]}")
    else:
        # 3-way tie: use the label of the image with centroid_rank == 1
        # (the single closest image to the cluster centre)
        tiebreak_row = grp[grp["centroid_rank"] == 1]
        if len(tiebreak_row) == 0:
            tiebreak_row = grp.sort_values("centroid_rank").iloc[[0]]
        chosen = tiebreak_row.iloc[0]["vibe"]
        cluster_vibes[cluster_id] = chosen
        print(f"  Cluster {cluster_id:2d}: {counter} → TIE-BREAK → {chosen}")

# ---------------------------------------------------------------------------
# Step 5 — Propagate and save final CSV
# ---------------------------------------------------------------------------
print("[5/5] Propagating labels to all 5,000 images...")
df_all["vibe"] = df_all["cluster_id"].map(cluster_vibes)

# Drop clusters whose winning label is DROP
df_keep = df_all[df_all["vibe"] != "DROP"].copy()
dropped_clusters = set(df_all["cluster_id"]) - set(df_keep["cluster_id"])

final = df_keep[["image_id", "vibe", "cluster_id"]].reset_index(drop=True)
final.to_csv(FINAL_CSV_PATH, index=False)

print(f"\nSummary:")
print(f"  Total images:         {len(df_all)}")
print(f"  Dropped clusters:     {len(dropped_clusters)} ({dropped_clusters})")
print(f"  Kept images:          {len(final)}")
print(f"  Class distribution:")
for vibe, cnt in sorted(final["vibe"].value_counts().items()):
    print(f"    {vibe:<30} {cnt}")
print(f"\nFinal CSV saved → {FINAL_CSV_PATH}")
print("\nNext step: run  3_train_model_v3.py")

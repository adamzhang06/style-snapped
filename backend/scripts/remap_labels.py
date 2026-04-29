"""
Option A remap: deterministic collapse for unambiguous merges, then re-run Gemini
only on former "Smart Casual / Office" rows to split into Business Casual / Business Formal.
"""
import os
import time

import google.generativeai as genai  # type: ignore
import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.environ["GEMINI_API_KEY"]
HF_TOKEN = os.getenv("HF_TOKEN")

if not API_KEY:
    raise ValueError("🚨 GEMINI_API_KEY not found!")
if not HF_TOKEN:
    raise ValueError("🚨 HF_TOKEN not found!")

CSV_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../my_vibe_model_2/synthetic_aesthetics.csv")
)

# --- STEP 1: Deterministic remap ---
REMAP = {
    "Boho Chic":             "Boho / Cottagecore",
    "Cottagecore":           "Boho / Cottagecore",
    "Grunge":                "Edgy / Alternative",
    "Y2K":                   "Edgy / Alternative",
    "Techwear / Gorpcore":   "Edgy / Alternative",
    "Old Money / Quiet Luxury": "Edgy / Alternative",
}

df = pd.read_csv(CSV_FILE)
before = df["vibe"].value_counts().to_dict()

df["vibe"] = df["vibe"].replace(REMAP)

remapped = {k: v for k, v in before.items() if k in REMAP}
print("Deterministic remaps applied:")
for old, new in REMAP.items():
    count = before.get(old, 0)
    print(f"  {old} ({count}) → {new}")

df.to_csv(CSV_FILE, index=False)
print(f"\n✓ Saved after deterministic remap.")

# --- STEP 2: Re-run Gemini on former Smart Casual / Office rows ---
smart_casual_mask = df["vibe"] == "Smart Casual / Office"
smart_casual_count = smart_casual_mask.sum()
print(f"\nRe-classifying {smart_casual_count} 'Smart Casual / Office' rows with Gemini...")

if smart_casual_count == 0:
    print("Nothing to re-classify. Done.")
    exit(0)

genai.configure(api_key=API_KEY)
gemini = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore

print("Loading HF dataset...")
dataset = load_dataset("ashraq/fashion-product-images-small", split="train", token=HF_TOKEN)
image_index = {str(item["id"]): item["image"] for item in dataset}
print(f"  Indexed {len(image_index)} images.")

split_prompt = """You are classifying a single professional clothing item into exactly one of two categories.

- Business Casual: chinos, oxford/button-down shirts, single blazers, smart separates — mix-and-match professional pieces, approachable but not strictly formal.
- Business Formal: full suits, dress shirts paired with formal trousers, matched suit jackets, ties — structured, formal, matched sets.

Output ONLY one of these exact phrases:
Business Casual
Business Formal"""

VALID = {"Business Casual", "Business Formal"}

for idx in df[smart_casual_mask].index:
    image_id = str(df.at[idx, "image_id"])
    image = image_index.get(image_id)
    if image is None:
        print(f"  ⚠ image_id {image_id} not found in dataset, skipping.")
        continue

    success = False
    retries = 0
    while not success and retries < 3:
        try:
            response = gemini.generate_content(contents=[image, split_prompt])
            result = response.text.strip()
            if result in VALID:
                df.at[idx, "vibe"] = result
                success = True
            else:
                print(f"  ⚠ Unexpected response '{result}' for {image_id}, defaulting to Business Casual.")
                df.at[idx, "vibe"] = "Business Casual"
                success = True
        except Exception as e:
            error_msg = str(e)
            retries += 1
            if "503" in error_msg or "500" in error_msg:
                print(f"  ⚠ Server error at {image_id}, retry {retries}/3...")
                time.sleep(3)
            else:
                print(f"  ❌ Error at {image_id}: {e}")
                time.sleep(5)

    # Save every 20 rows
    if idx % 20 == 0:
        df.to_csv(CSV_FILE, index=False)

df.to_csv(CSV_FILE, index=False)

print("\n✅ Remap complete. Final distribution:")
print(df[df["vibe"] != "DROP"]["vibe"].value_counts().to_string())
print(f"\nSaved to {CSV_FILE}")

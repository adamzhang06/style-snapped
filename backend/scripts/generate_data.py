import time
import pandas as pd
import os
import google.generativeai as genai
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# --- CONFIGURATION ---
API_KEY = os.environ["GEMINI_API_KEY"]
HF_TOKEN = os.getenv("HF_TOKEN")

if not API_KEY:
    raise ValueError("🚨 GEMINI_API_KEY not found!")
if not HF_TOKEN:
    raise ValueError("🚨 HF_TOKEN not found! Add it to your .env file.")

NUM_SAMPLES = 5000
CSV_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "../my_vibe_model_2/synthetic_aesthetics.csv"))

genai.configure(api_key=API_KEY) #type: ignore
# Remove the 'models/' prefix to prevent duplication errors
model = genai.GenerativeModel('gemini-2.5-flash') #type: ignore

# All support for the `google.generativeai` package has ended. It will no longer be receiving 
# updates or bug fixes. Please switch to the `google.genai` package as soon as possible.
# See README for more details:
# https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md

print("Authenticating and loading dataset from Hugging Face...")
# 3. ADD THE TOKEN TO THE DATASET LOADER
dataset = load_dataset(
    "ashraq/fashion-product-images-small", 
    split="train",
    token=HF_TOKEN
)

categories = [
    "Streetwear", "Techwear / Gorpcore", "Y2K", "Old Money / Quiet Luxury", 
    "Cottagecore", "Athleisure", "Grunge", "Boho Chic", "Casual Basics", 
    "Smart Casual / Office", "Traditional / Ethnic Wear", "Loungewear / Sleepwear"
]

prompt = """
You are an expert fashion stylist classifying e-commerce clothing items.

STEP 1: THE FILTER (CRITICAL)
Look at the item. Is it a watch, wallet, belt, basic underwear, socks, standard footwear, or a highly generic accessory? 
If YES, you must output EXACTLY the word: DROP

STEP 2: CLASSIFICATION
If the item is a core clothing piece (shirt, pants, jacket, dress), classify it into the single BEST category below. 

AESTHETIC DEFINITIONS:
- Streetwear: Graphic tees, hoodies, bold sneakers, urban culture.
- Techwear / Gorpcore: Cargo pants, heavy jackets, utilitarian gear, weather-resistant materials.
- Y2K: Bright colors, crop tops, wide-leg denim, playful, early 2000s.
- Old Money / Quiet Luxury: High-end knitwear, tailored pieces, elegant. (NO sports logos).
- Cottagecore: Floral prints, flowy dresses, earthy tones, rustic and romantic.
- Athleisure: Gym wear, leggings, track pants, sports brand logos. (e.g., Nike, Puma).
- Grunge: Plaid flannels, distressed denim, dark/washed-out tones, edgy.
- Boho Chic: Flowy garments, earthy tones, fringe, festival wear.
- Casual Basics: Plain t-shirts, standard denim, simple unbranded hoodies. The ultimate neutral wardrobe staples.
- Smart Casual / Office: Button-down collared shirts, chinos, blazers, formal trousers, workwear.
- Traditional / Ethnic Wear: Kurtas, sarees, traditional tunics, cultural motifs. 
- Loungewear / Sleepwear: Pajamas, sweatpants, robes, extremely relaxed home wear.

Output ONLY the exact category name or the word DROP. Do not include any punctuation, markdown, or explanations.
"""

# --- IMPROVED INITIALIZATION ---
results = []
processed_ids = set() # Use a set for O(1) lookups

if os.path.exists(CSV_FILE):
    df_existing = pd.read_csv(CSV_FILE)
    # Ensure image_id is treated as a string to avoid matching issues
    processed_ids = set(df_existing['image_id'].astype(str).unique())
    results = df_existing.to_dict('records')
    print(f"⏩ Found {len(processed_ids)} existing unique labels. Resuming...")
else:
    print("🚀 Starting fresh local run...")

# --- THE IMPROVED LOOP ---
try:
    # Always loop through the full range; the skip logic handles the rest
    for i in range(NUM_SAMPLES):
        item = dataset[i] 
        image_id = str(item['id'])
        
        # SKIP LOGIC: If we already have this ID, skip it
        if image_id in processed_ids:
            continue
            
        image = item['image']
        
        success = False
        retries = 0
        while not success and retries < 3:
            try:
                response = model.generate_content(
                    contents=[image, prompt]
                )
                vibe = response.text.strip()
                
                if vibe not in categories and vibe != "DROP":
                    vibe = "Everyday Minimalist"
                
                results.append({"image_id": image_id, "vibe": vibe})
                processed_ids.add(image_id) # Mark as done
                success = True
            
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "500" in error_msg:
                    retries += 1
                    print(f"⚠️ Server blip (503) at {i}. Retry {retries}/3...")
                    time.sleep(3)
                else:
                    print(f"❌ Error at {i}: {e}")
                    time.sleep(5)
                    retries = 3 # Skip on fatal errors

        # Save every 20 images to your MacBook SSD
        if i % 20 == 0:
            pd.DataFrame(results).to_csv(CSV_FILE, index=False)
            if i % 100 == 0:
                print(f"📍 Progress: {i}/{NUM_SAMPLES} labeled.")

except KeyboardInterrupt:
    print("\n🛑 Stopped by user. Saving progress to CSV...")

finally:
    pd.DataFrame(results).to_csv(CSV_FILE, index=False)
    print(f"✅ Local labels saved to {CSV_FILE}")
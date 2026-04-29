<div align="center">

# Style Vibe Classifier

**Drop in an outfit photo. Get back an aesthetic.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.11-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![Model](https://img.shields.io/badge/Model-ResNet--50-orange?style=flat-square)
![Pipeline](https://img.shields.io/badge/Pipeline-Embed--Cluster--Label-8B5CF6?style=flat-square)

*Presented at the **Machine Learning at Purdue (ML@P)** Project Symposium*

</div>

---

## What It Does

Style Vibe Classifier is a full-stack AI web app that reads an outfit photo and returns its internet aesthetic — *Streetwear*, *Traditional / Ethnic Wear*, *Athleisure*, and so on. A user uploads an image through a minimal React interface; a FastAPI backend runs it through a fine-tuned ResNet-50 vision model and returns the predicted aesthetic with a confidence score.

The interesting part isn't the inference — it's how the training data was created. This project has gone through **three modeling iterations**, each solving a fundamental limitation of the one before it. The final pipeline labels ~88,000 images using only 300 VLM API calls.

---

## The Journey: Three Iterations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  v1 (Colab, 2024)          v2 (local MPS)             v3 (local MPS)        │
│  ─────────────────         ──────────────             ──────────────        │
│  Rule-based lookup  ──►    VLM labels every  ──►      Embed → Cluster →     │
│  table from          fix   image directly     fix     VLM on centroids      │
│  e-commerce meta     noisy  (slow + expensive) scale   only (300 calls)     │
│  4 classes           labels  ~5k images               ~88k images           │
│                              9 classes                 6 classes            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

```
┌─────────────────────────────────────┐      ┌──────────────────────────────────────┐
│          React Frontend             │      │          FastAPI Backend             │
│          (Vite + Tailwind)          │      │          (Uvicorn + PyTorch)         │
│                                     │      │                                      │
│  [ Drag & Drop Upload ]             │      │  POST /predict                       │
│  [ Image Preview      ]  ──────────▶│      │  ├─ PIL decode                       │
│  [ Check Vibe Button  ]  FormData   │      │  ├─ Resize → Normalize (224×224)     │
│  [ Result Badge       ]  ◀──────────│      │  ├─ ResNet-50 forward pass           │
│                                     │ JSON │  ├─ Softmax → top-3 confidence %     │
└─────────────────────────────────────┘      │  └─ classes.json → aesthetic string  │
                                             └──────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| Backend | FastAPI, Uvicorn, Python-Multipart |
| ML Runtime | PyTorch 2.x, Apple MPS (M-series) |
| Base Model | ResNet-50 (ImageNet pre-trained via `torchvision`) |
| Dataset | [`ashraq/fashion-product-images-small`](https://huggingface.co/datasets/ashraq/fashion-product-images-small) — ~88k fashion product images |
| VLM Oracle | Gemini (`google-generativeai` SDK) |
| Clustering | scikit-learn KMeans |

---

## Dataset

All three models use [`ashraq/fashion-product-images-small`](https://huggingface.co/datasets/ashraq/fashion-product-images-small) from the Hugging Face Hub — a curated subset of a Kaggle fashion product dataset with **~88,000 product images** spanning clothing, accessories, footwear, and bags. The dataset skews heavily toward Indian fashion e-commerce, which is why Traditional / Ethnic Wear becomes a large natural cluster and niche Western aesthetics (Grunge, Y2K) are underrepresented.

---

## Model Iteration 1 — Rule-Based Mapping

**Trained on:** Google Colab T4 GPU  
**Serving model:** none (superseded)

The first attempt used no external labels at all. The Hugging Face dataset includes e-commerce metadata columns (`usage`, `season`) for each product. We hand-authored a lookup table to map `(usage, season)` pairs to four aesthetic classes:

| Aesthetic | Rule |
|---|---|
| Techwear | `usage = Sports` AND `season ∈ {Winter, Fall}` |
| Streetwear | `usage = Sports` AND `season ∈ {Summer, Spring}` |
| Dark Academia | `usage = Formal` |
| Cottagecore | `usage ∈ {Casual, Ethnic}` AND `season ∈ {Summer, Spring}` |

A 4-class linear head was placed on top of `microsoft/resnet-50` and trained with the Hugging Face `Trainer` API for 4 epochs.

**Why this failed:** The rule-based labels are fundamentally wrong. A formal suit in winter is not Dark Academia — it's just a suit. The model learned the metadata artifacts, not visual aesthetics. Val accuracy plateaued at ~68%, but the predictions were often semantically nonsensical. The four classes were also chosen to match the metadata fields that happened to exist, not to reflect real aesthetic diversity.

---

## Model Iteration 2 — Direct VLM Labeling

**Scripts:** `backend/scripts/1_my_vibe_model/`  
**Artifacts:** `backend/1_my_vibe_model/`  
**Currently serving in:** `backend/main.py`

To escape rule-based noise, v2 bypasses metadata entirely and asks a vision-language model to look at each image directly.

### Label Generation (`generate_data.py`)

Each image is sent to Gemini with a two-step prompt:

**Step 1 — The Filter:** Is this a watch, belt, footwear, handbag, or plain accessory? If yes → `DROP`. This removes products that don't belong to any clothing aesthetic.

**Step 2 — Classification:** Assign the image to exactly one of the 12 aesthetic categories.

The script saves results incrementally and resumes from where it left off on interruption. After labeling ~5,400 images:

```
Drop rate from 5,408 labeled images
────────────────────────────────────
  Usable clothing items   ████████████░░░  43%   (~2,325 images)
  Dropped (accessories)   ░░░░░░░░████████  57%   (~3,083 images)
```

### The 12-Class Taxonomy (original)

| Class | Count | Bar |
|---|---|---|
| Casual Basics | 219 | `████████████████████████████████████████████` |
| Smart Casual / Office | 203 | `█████████████████████████████████████████` |
| Streetwear | 122 | `████████████████████████` |
| Traditional / Ethnic Wear | 121 | `████████████████████████` |
| Athleisure | 90 | `██████████████████` |
| Loungewear / Sleepwear | 27 | `█████` |
| Y2K | 20 | `████` |
| Boho Chic | 19 | `████` |
| Grunge | 11 | `██` |
| Old Money / Quiet Luxury | 9 | `█` |
| Cottagecore | 9 | `█` |
| Techwear / Gorpcore | 7 | `█` |

*Data from `eda_audit.ipynb` — hardcoded from the initial 2,000-label run.*

The tail classes (Grunge, Old Money, Cottagecore, Techwear) had fewer than 15 samples each — far too few for a vision model to learn a discriminative boundary. This motivated a label consolidation step (`remap_labels.py`):

```
Category Consolidation: 12 → 9 Classes
───────────────────────────────────────
  Kept as-is    ▶  Casual Basics, Streetwear, Athleisure,
                   Traditional / Ethnic Wear, Loungewear / Sleepwear

  Split into 2  ▶  Smart Casual / Office
                       → Business Casual
                       → Business Formal  (re-labeled with Gemini)

  Merged        ▶  Y2K + Grunge + Old Money + Techwear
                       → Edgy / Alternative
                   Boho Chic + Cottagecore
                       → Boho / Cottagecore
```

### Training (`train_student.py`)

- **Base:** ResNet-50 (ImageNet weights, `torchvision`)
- **Strategy:** Freeze all layers → unfreeze `layer4` → replace `fc` with `Dropout(0.4) → Linear(2048, 9)`
- **Loss:** `CrossEntropyLoss` with inverse-frequency class weights — prevents the model from ignoring the 7-sample Techwear class in favor of the 219-sample Casual Basics class
- **Optimizer:** Two-param-group Adam — `layer4` at `lr=1e-4` (slow, preserves ImageNet features), head at `lr=1e-3` (fast, learns the new classification boundary)
- **Augmentation:** `RandomResizedCrop + RandomHorizontalFlip + ColorJitter` on train; clean `Resize(224)` on val
- **Checkpointing:** Best val-accuracy epoch is saved; the file is never overwritten by a worse epoch
- **Hardware:** Apple MPS (M-series MacBook Pro)

**Limitation hit:** With ~685 training samples across 9 classes, fine-tuning `layer4` (~8M parameters) overfits. Train accuracy reaches ~98% while val accuracy stabilizes around 62–64%. The bottleneck is label quantity, not model capacity — which points directly to the v3 approach.

---

## Model Iteration 3 — Embed-Cluster-Label (Semi-Supervised)

**Scripts:** `backend/scripts/2_my_vibe_model/`  
**Artifacts:** `backend/2_my_vibe_model/`  
**Status:** Trained. Not yet deployed to `main.py`.

The core insight: VLM calls are expensive and slow, but they don't need to happen for every image. If visually similar images cluster together in embedding space, labeling only the cluster centers and propagating those labels to all members gives you a massive dataset for the cost of a handful of API calls.

### The Three-Script Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  Script 1: 1_embed_and_cluster.py                                               │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  88k images ──► headless ResNet-50 ──► 88k × 2048 embeddings                   │
│                 (fc = Identity)         (cached to embeddings.npy)              │
│                                                ↓                                │
│                                         KMeans(k=100)                           │
│                                                ↓                                │
│                                    100 clusters, each with                      │
│                                    ~880 images on average                       │
│                                                ↓                                │
│                                    For each cluster:                            │
│                                    find 3 images with min ‖v − centroid‖₂      │
│                                    → 300 centroid images total                  │
│                                    → saved to cluster_assignments.csv           │
│                                                                                 │
│  Script 2: 2_vlm_label_propagation.py                                           │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  300 centroid images ──► Gemini (3 labels per cluster)                          │
│                                ↓                                                │
│                         Majority vote per cluster                               │
│                         (2-1 or 3-0 → winner)                                  │
│                         (3-way tie → label of image closest to centroid wins)   │
│                                ↓                                                │
│                         56 clusters vote DROP → discarded                       │
│                         44 clusters keep a vibe label                           │
│                                ↓                                                │
│                         Propagate label to ALL members of each kept cluster     │
│                         → synthetic_aesthetics_v3.csv (41,366 labeled images)  │
│                                                                                 │
│  Script 3: 3_train_model_v3.py                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                 │
│  41k labeled images ──► ResNet-50 fine-tune ──► model_v3.pt + classes.json     │
│  (80/20 split)           30 epochs, MPS                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Why k=100 Instead of k=50?

The first run used k=50 and produced 7 classes. Increasing to k=100 was an attempt to surface niche aesthetics (Y2K, Grunge, Old Money) by giving them more representational budget. The result: those aesthetics still never won a cluster majority vote — confirming they genuinely don't exist in this dataset in sufficient quantity, not that the clustering resolution was too coarse.

### The DROP Rate Problem

```
k=100 Cluster Vote Results
──────────────────────────
  56 / 100 clusters voted DROP  ██████████████████████████████████████░░░░░░░░░░░░░  56%
  44 / 100 clusters kept        ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████████  44%

  Total images in dataset:       87,844
  Survived (non-DROP clusters):  41,366  (47%)
  Discarded:                     46,478  (53%)
```

More than half the dataset is accessories, footwear, handbags, and other non-clothing items. The VLM correctly identified this and voted DROP on those clusters. This is the dataset's composition, not a bug in the pipeline.

### Final Class Distribution (v3)

```
  Class distribution across 41,366 labeled images
  ─────────────────────────────────────────────────────────────────
  Casual Basics            █████████████████████████████████  16,212  (39.2%)
  Traditional / Ethnic Wear█████████████████                   6,851  (16.6%)
  Streetwear               ████████████████                    6,737  (16.3%)
  Smart Casual / Office    █████████████                       5,437  (13.1%)
  Athleisure               ████████████                        4,982  (12.0%)
  Boho Chic                ███                                 1,147   (2.8%)
  ─────────────────────────────────────────────────────────────────
  Imbalance ratio (max/min):  Casual Basics vs. Boho Chic = 14.1×
```

**Classes absent from v3:** Y2K, Old Money / Quiet Luxury, Cottagecore, Grunge, Loungewear / Sleepwear, Techwear / Gorpcore. These appeared as minority votes in a few clusters but never won a majority — confirming they are not represented in the source dataset in sufficient density.

### Training Highlights (`3_train_model_v3.py`)

- **41,366 labeled samples** vs. ~685 in v2 — 60× more training data
- Same ResNet-50 architecture and freeze strategy as v2
- `CosineAnnealingWarmRestarts(T_0=15)` — two LR warm restarts over 30 epochs to help escape local minima introduced by label noise from cluster boundary regions
- Inverse-frequency class weights on `CrossEntropyLoss` — critical given the 14× Boho Chic imbalance
- Epoch 1 already reached **83.0% val accuracy**, with val > train (sign of healthy generalization, not overfitting)

---

## Project Structure

```
style-vibe-classifier/
│
├── backend/
│   ├── 1_my_vibe_model/                  # Model 1 artifacts (direct VLM labeling)
│   │   ├── synthetic_aesthetics.csv      # ~5,400 Gemini-labeled rows (with DROPs)
│   │   ├── resnet50_vibe.pt              # trained weights — CURRENTLY SERVING
│   │   └── label_classes.json            # ordered list of 9 class names
│   │
│   ├── 2_my_vibe_model/                  # Model 2 artifacts (Embed-Cluster-Label)
│   │   ├── embeddings.npy                # (88k, 2048) float32 embedding matrix
│   │   ├── image_ids.json                # ordered list of HF image IDs
│   │   ├── cluster_assignments.csv       # every image → cluster_id, centroid_rank, dist
│   │   ├── centroid_labels.csv           # 300-row VLM audit log (3 per cluster)
│   │   ├── synthetic_aesthetics_v3.csv   # 41,366 propagated labels
│   │   ├── model_v3.pt                   # trained weights (not yet deployed)
│   │   └── classes.json                  # int → aesthetic string map
│   │
│   ├── scripts/
│   │   ├── .env                          # GEMINI_API_KEY + HF_TOKEN (not committed)
│   │   │
│   │   ├── 1_my_vibe_model/              # Scripts for Model 1
│   │   │   ├── generate_data.py          # Gemini VLM labeling pipeline (resumable)
│   │   │   ├── remap_labels.py           # 12→9 class consolidation + Gemini re-split
│   │   │   ├── train_student.py          # ResNet-50 fine-tuning (MPS)
│   │   │   ├── eval_student.py           # val-set report + single-image inference
│   │   │   └── eda_audit.ipynb           # distribution plots, drop rate, sample grids
│   │   │
│   │   └── 2_my_vibe_model/              # Scripts for Model 2 (run in order)
│   │       ├── 1_embed_and_cluster.py    # ResNet-50 embeddings + KMeans(k=100)
│   │       ├── 2_vlm_label_propagation.py# VLM on 300 centroids + majority vote
│   │       └── 3_train_model_v3.py       # fine-tune ResNet-50 on 41k labels
│   │
│   ├── main.py                           # FastAPI app + /predict endpoint
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx                       # Main UI component
    │   └── index.css                     # Tailwind entry
    ├── tailwind.config.js
    └── package.json
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Apple Silicon Mac (MPS backend) — training scripts will fall back to CPU on other hardware

### 1 — Backend

```bash
# From project root
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt

cd backend && uvicorn main:app --reload
# API live at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

### 3 — Environment Variables

Create `backend/scripts/.env`:

```
HF_TOKEN=your_huggingface_token
GEMINI_API_KEY=your_gemini_api_key
```

---

## Reproducing the Pipelines

### Model 1 — Direct VLM Labeling

```bash
cd backend/scripts/1_my_vibe_model

# Label images with Gemini (safe to interrupt — resumes automatically)
python generate_data.py

# Optional: consolidate 12 → 9 classes (re-runs Gemini on ambiguous rows)
python remap_labels.py

# Train ResNet-50
python train_student.py

# Evaluate saved model (full val report or single image)
python eval_student.py
python eval_student.py --image /path/to/photo.jpg
```

### Model 2 — Embed-Cluster-Label

```bash
cd backend/scripts/2_my_vibe_model

# Step 1: embed all ~88k images, cluster with KMeans(k=100)
# Embeddings are cached to embeddings.npy — safe to re-run
python 1_embed_and_cluster.py

# Step 2: VLM-label the 300 centroid images, propagate to all 88k
# Checkpoints every 10 labels — safe to interrupt and resume
python 2_vlm_label_propagation.py

# Step 3: train ResNet-50 on the 41k propagated labels
python 3_train_model_v3.py
```

---

## Design Decisions & Lessons Learned

**Why ResNet-50 and not a ViT or CLIP?**  
ResNet-50 is a well-understood backbone with a clean 2048-dim embedding space that compresses well into KMeans. CLIP embeddings would likely cluster more semantically, but the goal was a system that runs end-to-end locally on MPS without needing OpenAI API calls for the embedding step.

**Why majority vote across 3 centroid images instead of 1?**  
A single centroid image can be a boundary case — visually ambiguous between two aesthetics. Using 3 images gives the VLM a chance to "see" the cluster's range and reach a stable verdict. The tie-break rule (closest image to the mathematical centroid wins) is a principled fallback that favors the most archetypal member of the cluster.

**Why are 6 classes fewer than the 9 from v2, even with 100 clusters?**  
The dataset's true composition is the limiting factor. Niche Western aesthetics (Y2K, Grunge, Cottagecore, Old Money) simply don't have enough images in this particular dataset to form their own dense clusters. A 14× class imbalance (Casual Basics vs. Boho Chic) is what the dataset actually contains — no amount of re-clustering changes that. A dataset like DeepFashion or a scraped Instagram corpus would be needed to represent those aesthetics.

**Why `CosineAnnealingWarmRestarts` in v3 but not v2?**  
In v2, with ~685 training samples, the main problem was overfitting — adding LR restarts would have made it worse. In v3, with 41k samples, the training is stable enough that warm restarts help the optimizer escape the flat regions introduced by label noise at cluster boundaries.

---

## Model Comparison

| | Model 1 | Model 2 (serving) | Model 3 (trained) |
|---|---|---|---|
| **Labeling method** | Rule-based lookup | Gemini — every image | Gemini — 300 centroids only |
| **VLM calls** | 0 | ~5,400 | 300 |
| **Training samples** | ~44k (noisy) | ~685 (clean) | ~41k (propagated) |
| **Classes** | 4 | 9 | 6 |
| **Val accuracy** | ~68% (semantically wrong) | ~64% | 83%+ (ep. 1) |
| **Hardware** | Colab T4 | Apple MPS | Apple MPS |

---

<div align="center">

Built for the **ML@P Project Symposium** · Purdue University

</div>

<div align="center">

# Style Vibe Classifier

**Drop in an outfit photo. Get back an aesthetic.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.11-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗-Transformers-FFD21E?style=flat-square)
![Accuracy](https://img.shields.io/badge/Val%20Accuracy-64.0%25-8B5CF6?style=flat-square)

*Presented at the **Machine Learning at Purdue (ML@P)** Project Symposium*

</div>

---

## Overview

Style Vibe Classifier is a full-stack AI web application that classifies outfit photos into contemporary internet aesthetics. A user uploads an image through a minimal React interface; the image is sent to a FastAPI backend, which runs it through a fine-tuned ResNet-50 vision model and returns the predicted aesthetic and a confidence percentage.

The project has gone through two modeling iterations, each addressing a core limitation of the previous approach.

---

## Architecture

```
┌─────────────────────────────────────┐      ┌──────────────────────────────────────┐
│          React Frontend             │      │          FastAPI Backend             │
│          (Vite + Tailwind)          │      │          (Uvicorn + PyTorch)         │
│                                     │      │                                      │
│  [ Drag & Drop Upload ]             │      │  POST /predict                       │
│  [ Image Preview      ]  ──────────▶│      │  ├─ PIL decode                       │
│  [ Check Vibe Button  ]  FormData   │      │  ├─ AutoImageProcessor               │
│  [ Result Badge       ]  ◀──────────│      │  ├─ ResNet-50 forward pass           │
│                                     │ JSON │  ├─ Softmax → confidence %           │
└─────────────────────────────────────┘      │  └─ id2label → aesthetic string      │
                                             └──────────────────────────────────────┘
```

### Tech Stack

| Layer      | Technology                                                              |
|------------|-------------------------------------------------------------------------|
| Frontend   | React 19, Vite, Tailwind CSS, Axios                                     |
| Backend    | FastAPI, Uvicorn, Python-Multipart                                      |
| ML Runtime | PyTorch, Hugging Face `transformers`                                    |
| Training   | PyTorch (local, Apple MPS), Hugging Face `datasets`, Google Colab (v1) |
| Labeling   | Gemini 2.5 Flash (vision) via `google-generativeai`                     |
| Base Model | [`microsoft/resnet-50`](https://huggingface.co/microsoft/resnet-50)     |

---

## Data & Modeling

Both models use [`ashraq/fashion-product-images-small`](https://huggingface.co/datasets/ashraq/fashion-product-images-small) from the Hugging Face Hub — a curated subset of a Kaggle fashion product dataset with ~44,000 product images.

---

### Model v1 — Rule-Based Mapping (ML@P Symposium)

The original model mapped the dataset's existing `(usage, season)` e-commerce metadata into four aesthetic classes using a hand-written lookup table:

| Aesthetic         | Mapping Logic                                                       |
|-------------------|---------------------------------------------------------------------|
| **Techwear**      | `usage = Sports` and `season ∈ {Winter, Fall}`                     |
| **Streetwear**    | `usage = Sports` and `season ∈ {Summer, Spring}`                   |
| **Dark Academia** | `usage = Formal`                                                    |
| **Cottagecore**   | `usage ∈ {Casual, Ethnic}` and `season ∈ {Summer, Spring}`         |

- **Head:** 4-class linear classifier on top of `microsoft/resnet-50`
- **Training:** Hugging Face `Trainer` API, 4 epochs on a Colab T4 GPU
- **Val accuracy:** ~68.2%
- **Limitation:** The 4 classes were chosen to fit the metadata, not to reflect real aesthetic diversity. The rule-based labels are noisy — "Formal" maps neatly to Dark Academia in the lookup table, but not in reality.

---

### Model v2 — Synthetic Labeling with Gemini Vision

To break out of the constraints of rule-based mapping, v2 uses a **vision-language model to directly label images** from scratch, enabling a much richer 12-class taxonomy.

#### Label Generation (`backend/scripts/generate_data.py`)

Each of the first 2,000 images in the dataset is sent to **Gemini 2.5 Flash** with a two-step prompt:

1. **Filter step:** Reject accessories, footwear, and generic basics that don't belong to any aesthetic (labeled `DROP`).
2. **Classification step:** Assign the image to the single best-matching aesthetic from the 12 classes below.

The script saves results incrementally to `backend/my_vibe_model_2/synthetic_aesthetics.csv` and resumes from where it left off if interrupted.

#### Class Taxonomy (12 classes)

| Class | Description |
|---|---|
| **Athleisure** | Gym wear, leggings, track pants, sports brand logos |
| **Boho Chic** | Flowy garments, earthy tones, fringe, festival wear |
| **Casual Basics** | Plain tees, standard denim, simple unbranded hoodies |
| **Cottagecore** | Floral prints, flowy dresses, earthy tones, rustic |
| **Grunge** | Plaid flannels, distressed denim, dark washed-out tones |
| **Loungewear / Sleepwear** | Pajamas, sweatpants, robes, relaxed home wear |
| **Old Money / Quiet Luxury** | High-end knitwear, tailored pieces, no sports logos |
| **Smart Casual / Office** | Button-downs, chinos, blazers, formal trousers |
| **Streetwear** | Graphic tees, hoodies, bold sneakers, urban culture |
| **Techwear / Gorpcore** | Cargo pants, heavy jackets, utilitarian/weather-resistant gear |
| **Traditional / Ethnic Wear** | Kurtas, sarees, traditional tunics, cultural motifs |
| **Y2K** | Bright colors, crop tops, wide-leg denim, early 2000s |

Of the 2,000 labeled samples, **857 passed the filter** (the rest were DROPs). The dataset is class-imbalanced — Casual Basics and Smart Casual/Office dominate, while Techwear, Cottagecore, and Grunge have fewer than 15 samples each.

#### Training (`backend/scripts/train_student.py`)

- **Base model:** ResNet-50 (ImageNet pre-trained)
- **Strategy:** Freeze all layers → replace the classification head → unfreeze `layer4` for fine-tuning
- **Head:** `Dropout(0.4) → Linear(2048, 12)` — dropout regularizes the head to reduce memorization of the small training set
- **Loss:** `CrossEntropyLoss` with inverse-frequency class weights to prevent the model from ignoring tail classes
- **Data augmentation:** Training images use `RandomResizedCrop`, `RandomHorizontalFlip`, and `ColorJitter` to multiply effective training signal; validation uses a clean resize-only transform
- **Optimizer:** Adam with two param groups and weight decay — `layer4` at `lr=1e-4`, head at `lr=1e-3`; lower LR for `layer4` prevents the fine-tuned backbone features from being overwritten too aggressively
- **Checkpointing:** Only the epoch with the best validation accuracy is saved, so the final model is never overwritten by a worse epoch
- **Epochs:** 30 (best checkpoint at epoch 23, ~62.8% val accuracy)
- **Hardware:** Apple Silicon MPS (local)
- **Outputs:** `my_vibe_model_2/resnet50_vibe.pt`, `my_vibe_model_2/label_classes.json`

The image index for the 44k-item HF dataset is built once as a Python dict at load time so every `__getitem__` call is O(1).

> **Current ceiling:** With 685 training samples across 12 classes, fine-tuning `layer4` (~8M parameters) still overfits — train accuracy reaches ~98% while val stabilizes around 60-63%. Labeling more images (targeting 200+ samples per class) is the highest-leverage next step.

#### Evaluation (`backend/scripts/eval_student.py`)

```bash
# Full validation report (per-class precision/recall + confusion matrix)
python scripts/eval_student.py

# Quick inference on a single image (local path or URL)
python scripts/eval_student.py --image /path/to/photo.jpg
```

High-data classes (Streetwear, Traditional/Ethnic Wear, Smart Casual/Office) achieve F1 scores in the 0.60–0.70 range. Tail classes with fewer than 15 training samples are the primary remaining weakness — more labels are the highest-leverage next step.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1 — Backend

```bash
# Create and activate a virtual environment (from project root)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the server
cd backend && uvicorn main:app --reload
```

The API will be live at `http://localhost:8000`.  
Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### 2 — Frontend

```bash
cd frontend

npm install
npm run dev
```

The app will open at `http://localhost:5173`.

### 3 — Retrain Model v2 (optional)

To generate new labels or retrain from scratch, add a `.env` file to `backend/scripts/`:

```
HF_TOKEN=your_huggingface_token
GEMINI_API_KEY=your_gemini_key   # only needed for generate_data.py
```

```bash
cd backend/scripts

# Re-label images with Gemini (resumes from existing CSV automatically)
python generate_data.py

# Train ResNet-50 on the labels
python train_student.py

# Evaluate the saved model
python eval_student.py
```

---

### Usage

1. Ensure the backend is running on port `8000`
2. Open the frontend at `http://localhost:5173`
3. Drag and drop (or click to upload) an outfit photo
4. Hit **Check Vibe**
5. The predicted aesthetic and confidence score appear below

---

## Project Structure

```
style-vibe-classifier/
├── backend/
│   ├── my_vibe_model/               # v1 model (HF format, not committed)
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   └── preprocessor_config.json
│   ├── my_vibe_model_2/             # v2 model artifacts
│   │   ├── synthetic_aesthetics.csv # 2000 Gemini-labeled samples
│   │   ├── resnet50_vibe.pt         # trained weights (not committed)
│   │   └── label_classes.json       # ordered list of 12 class names
│   ├── scripts/
│   │   ├── generate_data.py         # Gemini vision labeling pipeline
│   │   ├── train_student.py         # ResNet-50 fine-tuning (local MPS)
│   │   └── eval_student.py          # val-set report + single-image inference
│   ├── main.py                      # FastAPI app + /predict endpoint
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx                  # Main UI component
    │   └── index.css                # Tailwind entry
    ├── tailwind.config.js
    └── package.json
```

---

## Training Notebook (v1)

The original v1 training pipeline is documented in our Google Colab notebook:

**[Open in Google Colab →](https://colab.research.google.com/drive/1_xECWTdAYuafsXn-wJk3WBEluadR0bxr?usp=sharing)**

---

<div align="center">

Built for the **ML@P Project Symposium** · Purdue University

</div>

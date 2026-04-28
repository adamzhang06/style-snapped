<div align="center">

# Style Vibe Classifier

**Drop in an outfit photo. Get back an aesthetic.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![PyTorch](https://img.shields.io/badge/PyTorch-2.11-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/🤗-Transformers-FFD21E?style=flat-square)
![Accuracy](https://img.shields.io/badge/Val%20Accuracy-68.2%25-8B5CF6?style=flat-square)

*Presented at the **Machine Learning at Purdue (ML@P)** Project Symposium*

</div>

---

## Overview

Style Vibe Classifier is a full-stack AI web application that classifies outfit photos into one of four contemporary internet aesthetics: **Techwear**, **Streetwear**, **Dark Academia**, and **Cottagecore**.

A user uploads an image through a minimal React interface. The image is sent to a FastAPI backend, which runs it through a fine-tuned ResNet-50 vision model and returns the predicted aesthetic and a confidence percentage — all in under a second on CPU.

The core ML challenge was not the architecture itself, but the **dataset curation**: the source data carries e-commerce product tags, not aesthetic labels. We wrote a custom mapping layer to bridge that gap, turning standard retail metadata into culturally meaningful style categories.

---

## Architecture

```
┌─────────────────────────────────────┐      ┌──────────────────────────────────────┐
│          React Frontend             │      │          FastAPI Backend              │
│          (Vite + Tailwind)          │      │          (Uvicorn + PyTorch)          │
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

| Layer      | Technology                                               |
|------------|----------------------------------------------------------|
| Frontend   | React 19, Vite, Tailwind CSS, Axios                      |
| Backend    | FastAPI, Uvicorn, Python-Multipart                       |
| ML Runtime | PyTorch, Hugging Face `transformers`                     |
| Training   | Hugging Face `datasets`, `Trainer` API, Google Colab     |
| Base Model | [`microsoft/resnet-50`](https://huggingface.co/microsoft/resnet-50) |

---

## Data & Modeling

### Dataset

We used [`ashraq/fashion-product-images-small`](https://huggingface.co/datasets/ashraq/fashion-product-images-small) from the Hugging Face Hub — a curated subset of a Kaggle fashion product dataset containing product images alongside e-commerce metadata such as `usage` (e.g., Casual, Formal, Sports) and `season` (Summer, Winter, Spring, Fall).

### Aesthetic Mapping

The dataset ships with retail tags, not aesthetic labels. We wrote a custom mapping function in our training notebook to translate the `(usage, season)` metadata pairs into the four target classes:

| Aesthetic      | Mapping Logic                                          |
|----------------|--------------------------------------------------------|
| **Techwear**   | `usage = Sports` **and** `season ∈ {Winter, Fall}`    |
| **Streetwear** | `usage = Sports` **and** `season ∈ {Summer, Spring}`  |
| **Dark Academia** | `usage = Formal`                                  |
| **Cottagecore**| `usage ∈ {Casual, Ethnic}` **and** `season ∈ {Summer, Spring}` |

Samples that didn't cleanly fit a category were dropped to keep label noise low.

### Fine-Tuning

- **Base model:** `microsoft/resnet-50` (ImageNet pre-trained)
- **Head:** replaced with a 4-class linear classifier
- **Epochs:** 4
- **Validation accuracy:** ~68.2%
- **Framework:** Hugging Face `Trainer` API on a Colab T4 GPU

The model and processor are exported via `save_pretrained()` and loaded locally at backend startup with `AutoModelForImageClassification` and `AutoImageProcessor`.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- The fine-tuned model folder (`my_vibe_model/`)

> **Model folder:** After training, download the `my_vibe_model/` directory from Colab and place it at `backend/my_vibe_model/`. It should contain `config.json`, `model.safetensors`, and `preprocessor_config.json`.

---

### 1 — Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

The API will be live at `http://localhost:8000`.  
Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

### 2 — Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will open at `http://localhost:5173`.

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
│   ├── my_vibe_model/          # Fine-tuned model (not committed — see setup)
│   │   ├── config.json
│   │   ├── model.safetensors
│   │   └── preprocessor_config.json
│   ├── main.py                 # FastAPI app + /predict endpoint
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main UI component
    │   └── index.css           # Tailwind entry
    ├── tailwind.config.js
    └── package.json
```

---

## Training Notebook

The full training pipeline — data loading, aesthetic mapping, fine-tuning, and model export — is documented in our Google Colab notebook:

**[Open in Google Colab →](https://colab.research.google.com/drive/1_xECWTdAYuafsXn-wJk3WBEluadR0bxr?usp=sharing)**

The notebook covers:
- Loading `ashraq/fashion-product-images-small` via the `datasets` library
- Applying the `(usage, season) → aesthetic` mapping function
- Preprocessing images with `AutoImageProcessor`
- Fine-tuning ResNet-50 with the Hugging Face `Trainer` API
- Evaluating on the validation split
- Exporting the model with `save_pretrained()` for local deployment

---

<div align="center">

Built for the **ML@P Project Symposium** · Purdue University

</div>

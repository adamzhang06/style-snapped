import io
from pathlib import Path

import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_DIR = Path(__file__).parent / "my_vibe_model"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    processor = AutoImageProcessor.from_pretrained(MODEL_DIR)
    model = AutoModelForImageClassification.from_pretrained(MODEL_DIR)
    model.eval()
    print(f"✓ Model loaded from {MODEL_DIR}")
except Exception as e:
    print(f"⚠ Failed to load model from {MODEL_DIR}: {e}")
    processor = None
    model = None


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        logits = model(**inputs).logits

    probabilities = torch.softmax(logits, dim=-1)[0]
    confidence, predicted_idx = probabilities.max(dim=-1)

    vibe = model.config.id2label[predicted_idx.item()]

    return {"vibe": vibe, "confidence": round(confidence.item() * 100, 1)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

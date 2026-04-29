import io
import json
from pathlib import Path

import torch
import torch.nn as nn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from torchvision import models, transforms

# --- New model (ResNet50, my_vibe_model_2) ---
MODEL_DIR = Path(__file__).parent / "my_vibe_model_2"

# --- Old model (HuggingFace ViT, my_vibe_model) ---
# from transformers import AutoImageProcessor, AutoModelForImageClassification
# MODEL_DIR = Path(__file__).parent / "my_vibe_model"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- New model loading ---
try:
    with open(MODEL_DIR / "label_classes.json") as f:
        label_classes = json.load(f)

    num_classes = len(label_classes)
    _resnet = models.resnet50(weights=None)
    _resnet.fc = nn.Sequential( #type: ignore[assignment]
        nn.Dropout(p=0.4),
        nn.Linear(_resnet.fc.in_features, num_classes),
    )
    _resnet.load_state_dict(torch.load(MODEL_DIR / "resnet50_vibe.pt", map_location="cpu"))
    _resnet.eval()
    model = _resnet
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    print(f"✓ ResNet50 model loaded from {MODEL_DIR} ({num_classes} classes)")
except Exception as e:
    print(f"⚠ Failed to load model from {MODEL_DIR}: {e}")
    model = None
    transform = None
    label_classes = []

# --- Old model loading ---
# try:
#     processor = AutoImageProcessor.from_pretrained(MODEL_DIR)
#     model = AutoModelForImageClassification.from_pretrained(MODEL_DIR)
#     model.eval()
#     print(f"✓ Model loaded from {MODEL_DIR}")
# except Exception as e:
#     print(f"⚠ Failed to load model from {MODEL_DIR}: {e}")
#     processor = None
#     model = None


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    # --- New model inference ---
    tensor = transform(image).unsqueeze(0) #type: ignore[call-overload]
    with torch.no_grad():
        logits = model(tensor) #type: ignore[call]
    probabilities = torch.softmax(logits, dim=-1)[0]
    confidence, predicted_idx = probabilities.max(dim=-1)
    vibe = label_classes[predicted_idx.item()] #type: ignore[index]

    # --- Old model inference ---
    # inputs = processor(images=image, return_tensors="pt")
    # with torch.no_grad():
    #     logits = model(**inputs).logits
    # probabilities = torch.softmax(logits, dim=-1)[0]
    # confidence, predicted_idx = probabilities.max(dim=-1)
    # vibe = model.config.id2label[predicted_idx.item()]

    return {"vibe": vibe, "confidence": round(confidence.item() * 100, 1)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

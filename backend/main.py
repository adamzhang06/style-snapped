import io
import json
from pathlib import Path

import torch
import torch.nn as nn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from torchvision import models, transforms

# --- Model 1 (ResNet50, 1_my_vibe_model) ---
MODEL_DIR = Path(__file__).parent / "1_my_vibe_model"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    with open(MODEL_DIR / "label_classes.json") as f:
        label_classes = json.load(f)

    num_classes = len(label_classes)
    _resnet = models.resnet50(weights=None)
    _resnet.fc = nn.Sequential(  # type: ignore[assignment]
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


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    tensor = transform(image).unsqueeze(0)  # type: ignore[call-overload]
    with torch.no_grad():
        logits = model(tensor)  # type: ignore[call]
    probabilities = torch.softmax(logits, dim=-1)[0]

    top_probs, top_idxs = probabilities.topk(min(3, len(label_classes)))
    top_k = [
        {"vibe": label_classes[idx.item()], "confidence": round(prob.item() * 100, 1)}  # type: ignore[index]
        for idx, prob in zip(top_idxs, top_probs)
    ]
    return {"vibe": top_k[0]["vibe"], "confidence": top_k[0]["confidence"], "top_k": top_k}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

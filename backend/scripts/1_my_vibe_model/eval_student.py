"""
Evaluate the saved ResNet-50 vibe classifier.

Usage:
  # Full val-set report (confusion matrix + per-class accuracy)
  python eval_student.py

  # Quick inference on a single local image or URL
  python eval_student.py --image /path/to/image.jpg
  python eval_student.py --image https://example.com/photo.jpg
"""

import argparse
import json
import os

import pandas as pd
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report
from tqdm import tqdm
from PIL import Image
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "..", "..", "1_my_vibe_model")
MODEL_PATH = os.path.join(MODEL_DIR, "resnet50_vibe.pt")
LABELS_PATH = os.path.join(MODEL_DIR, "label_classes.json")
DATA_PATH = os.path.join(MODEL_DIR, "synthetic_aesthetics.csv")

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def load_model(num_classes):
    model = models.resnet50(weights=None)
    model.fc = nn.Sequential(  # type: ignore[assignment]
        nn.Dropout(p=0.4),
        nn.Linear(model.fc.in_features, num_classes),
    )
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    return model


class VibeDataset(Dataset):
    def __init__(self, dataframe, image_index):
        self.dataframe = dataframe.reset_index(drop=True)
        self.image_index = image_index

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        image = self.image_index[int(row["image_id"])].convert("RGB")  # type: ignore[index]
        return transform(image), int(row["label"])


def eval_val_set():
    with open(LABELS_PATH) as f:
        classes = json.load(f)
    num_classes = len(classes)

    df = pd.read_csv(DATA_PATH)
    df_clean = df[df["vibe"] != "DROP"].copy()
    encoder = LabelEncoder()
    encoder.fit(classes)
    df_clean["label"] = encoder.transform(df_clean["vibe"]) #type: ignore[assignment]

    _, val_df = train_test_split(df_clean, test_size=0.2, random_state=42, stratify=df_clean["label"])

    print("Loading HF dataset...")
    hf_dataset = load_dataset("ashraq/fashion-product-images-small", split="train", token=HF_TOKEN)
    image_index = {item["id"]: item["image"] for item in hf_dataset}  # type: ignore[index]

    val_loader = DataLoader(VibeDataset(val_df, image_index), batch_size=32, shuffle=False, num_workers=0)

    model = load_model(num_classes)
    print(f"Model loaded from {MODEL_PATH}\n")

    all_preds = []
    all_labels = []
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Evaluating"):
            outputs = model(images.to(device))
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().tolist())
            all_labels.extend(labels.tolist())

    print(classification_report(all_labels, all_preds, target_names=classes, digits=3, zero_division=0))

    print("Confusion matrix (rows=actual, cols=predicted):")
    cm = confusion_matrix(all_labels, all_preds)
    header = f"{'':30s}" + "".join(f"{c[:6]:>8}" for c in classes)
    print(header)
    for i, row in enumerate(cm):
        print(f"{classes[i]:30s}" + "".join(f"{v:>8}" for v in row))


def eval_single_image(image_path: str):
    with open(LABELS_PATH) as f:
        classes = json.load(f)

    model = load_model(len(classes))

    if image_path.startswith("http://") or image_path.startswith("https://"):
        import urllib.request
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            urllib.request.urlretrieve(image_path, tmp.name)
            image_path = tmp.name

    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device) #type: ignore[assignment]

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        top5 = torch.topk(probs, k=min(5, len(classes)))

    print("Top predictions:")
    for score, idx in zip(top5.values.tolist(), top5.indices.tolist()):
        bar = "█" * int(score * 30)
        print(f"  {classes[idx]:30s} {score*100:5.1f}%  {bar}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None, help="Path or URL to a single image")
    args = parser.parse_args()

    if args.image:
        eval_single_image(args.image)
    else:
        eval_val_set()

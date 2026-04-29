"""
Script 3: Fine-tune ResNet-50 on the propagated labels from Script 2.

Reads:   backend/my_vibe_model_3/synthetic_aesthetics_v3.csv
Writes:  backend/my_vibe_model_3/model_v3.pt
         backend/my_vibe_model_3/classes.json
"""

import os
import json

import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH   = os.path.join(SCRIPT_DIR, "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found — add it to backend/scripts/.env")

OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "2_my_vibe_model"))
DATA_PATH  = os.path.join(OUTPUT_DIR, "synthetic_aesthetics_v3.csv")
MODEL_PATH = os.path.join(OUTPUT_DIR, "model_v3.pt")
CLASSES_PATH = os.path.join(OUTPUT_DIR, "classes.json")

EPOCHS      = 30
BATCH_SIZE  = 32
LR_HEAD     = 1e-3
LR_LAYER4   = 1e-4
WEIGHT_DECAY = 1e-4
DROPOUT     = 0.4

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"[Setup] Training on device: {device}")

# ---------------------------------------------------------------------------
# Step 1 — Load and encode labels
# ---------------------------------------------------------------------------
print("[1/5] Loading labels from synthetic_aesthetics_v3.csv...")
df = pd.read_csv(DATA_PATH)

# Guard: remove any DROP rows that slipped through
df = df[df["vibe"] != "DROP"].copy()

encoder = LabelEncoder()
df["label"] = encoder.fit_transform(df["vibe"])  # type: ignore[assignment]
num_classes  = len(encoder.classes_)
print(f"      {len(df)} labeled samples | {num_classes} classes:")
for i, cls in enumerate(encoder.classes_):
    count = (df["label"] == i).sum()
    print(f"        [{i:2d}] {cls:<30} {count} images")

# Stratified 80/20 split
train_df, val_df = train_test_split(
    df, test_size=0.2, random_state=42, stratify=df["label"]
)
print(f"\n      Train: {len(train_df)} | Val: {len(val_df)}")

# ---------------------------------------------------------------------------
# Step 2 — Load dataset and build image index
# ---------------------------------------------------------------------------
print("[2/5] Loading HuggingFace dataset and building image index...")
hf_dataset = load_dataset(
    "ashraq/fashion-product-images-small",
    split="train",
    token=HF_TOKEN,
)
needed_ids = set(df["image_id"].astype(int).tolist())
image_index = {}
for item in hf_dataset:  # type: ignore[union-attr]
    if item["id"] in needed_ids:  # type: ignore[index]
        image_index[item["id"]] = item["image"]  # type: ignore[index]
print(f"      Indexed {len(image_index)} images.")

# ---------------------------------------------------------------------------
# Step 3 — Dataset and DataLoaders
# ---------------------------------------------------------------------------
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


class VibeDataset(Dataset):
    def __init__(self, dataframe: pd.DataFrame, image_index: dict, transform):
        self.df        = dataframe.reset_index(drop=True)
        self.idx       = image_index
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, i: int):
        row   = self.df.iloc[i]
        img   = self.idx[int(row["image_id"])]
        if img.mode != "RGB":
            img = img.convert("RGB")
        return self.transform(img), int(row["label"])


# num_workers=0 is required on MPS
train_loader = DataLoader(
    VibeDataset(train_df, image_index, train_transform),
    batch_size=BATCH_SIZE, shuffle=True, num_workers=0,
)
val_loader = DataLoader(
    VibeDataset(val_df, image_index, val_transform),
    batch_size=BATCH_SIZE, shuffle=False, num_workers=0,
)

# ---------------------------------------------------------------------------
# Step 4 — Model architecture
# ---------------------------------------------------------------------------
print(f"[3/5] Building ResNet-50 for {num_classes} classes...")
model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

# Freeze everything first, then unfreeze layer4 for fine-tuning
for param in model.parameters():
    param.requires_grad = False
for param in model.layer4.parameters():
    param.requires_grad = True

in_features = model.fc.in_features
model.fc = nn.Sequential(  # type: ignore[assignment]
    nn.Dropout(p=DROPOUT),
    nn.Linear(in_features, num_classes),
)
model = model.to(device)

# Inverse-frequency class weights to handle imbalance from cluster propagation
label_counts  = df["label"].value_counts().sort_index()
class_weights = (1.0 / label_counts).to_numpy(dtype=float)
class_weights = class_weights / class_weights.sum() * num_classes
weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)
criterion = nn.CrossEntropyLoss(weight=weights_tensor)

# Two param groups: slow for layer4 backbone, fast for new head
optimizer = optim.Adam([
    {"params": model.layer4.parameters(), "lr": LR_LAYER4, "weight_decay": WEIGHT_DECAY},
    {"params": model.fc.parameters(),     "lr": LR_HEAD,   "weight_decay": WEIGHT_DECAY},
])

# Cosine annealing restarts: warms up twice over 30 epochs, each T_0=15 epochs
scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=15, T_mult=1, eta_min=1e-6
)

# ---------------------------------------------------------------------------
# Step 5 — Training loop
# ---------------------------------------------------------------------------
print(f"[4/5] Training for {EPOCHS} epochs...\n")

best_val_acc = 0.0
best_epoch   = 0

for epoch in range(EPOCHS):
    # --- Train ---
    model.train()
    running_loss = 0.0
    correct = 0
    total   = 0

    bar = tqdm(train_loader, desc=f"Epoch {epoch+1:02d}/{EPOCHS} [train]")
    for images, labels in bar:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss    = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total   += labels.size(0)
        correct += (predicted == labels).sum().item()
        bar.set_postfix(loss=f"{loss.item():.3f}",
                        acc=f"{100.*correct/total:.1f}%")

    scheduler.step()
    train_acc  = 100. * correct / total
    train_loss = running_loss / len(train_loader)

    # --- Validate ---
    model.eval()
    val_correct = 0
    val_total   = 0
    val_loss    = 0.0

    with torch.no_grad():
        for images, labels in tqdm(val_loader,
                                   desc=f"Epoch {epoch+1:02d}/{EPOCHS} [val]  ",
                                   leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss    = criterion(outputs, labels)
            val_loss   += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            val_total   += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_acc  = 100. * val_correct / val_total
    val_loss /= len(val_loader)

    marker = ""
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_epoch   = epoch + 1
        torch.save(model.state_dict(), MODEL_PATH)
        marker = "  ← best"

    print(f"  Epoch {epoch+1:02d}: "
          f"train_loss={train_loss:.4f}  train_acc={train_acc:.1f}%  |  "
          f"val_loss={val_loss:.4f}  val_acc={val_acc:.1f}%{marker}")

# ---------------------------------------------------------------------------
# Step 6 — Save class mapping
# ---------------------------------------------------------------------------
print(f"\n[5/5] Saving artefacts...")
classes_map = {int(i): str(cls) for i, cls in enumerate(encoder.classes_)}
with open(CLASSES_PATH, "w") as f:
    json.dump(classes_map, f, indent=2)

print(f"\n{'='*60}")
print(f"  Best val accuracy : {best_val_acc:.2f}%  (epoch {best_epoch})")
print(f"  Model weights     → {MODEL_PATH}")
print(f"  Class map         → {CLASSES_PATH}")
print(f"{'='*60}")
print("Training complete!")

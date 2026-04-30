"""
Script 2: Fine-tune ResNet-50 on web-scraped fashion images.

Two-phase training:
  Phase 1 (epochs 1-10)  — freeze backbone, train only the classifier head
  Phase 2 (epochs 11-30) — unfreeze layer4 + head, train with lower LR

Best val accuracy checkpoint saved as model.pt.

Outputs (backend/3_my_vibe_model/):
  model.pt       — best checkpoint (state dict)
  classes.json   — {"0": "Athleisure", "1": "Boho / Cottagecore", ...}
"""

import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms
from sklearn.preprocessing import LabelEncoder
import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
BACKEND_DIR  = SCRIPT_DIR.parent.parent
MODEL3_DIR   = BACKEND_DIR / "3_my_vibe_model"
DATA_DIR     = MODEL3_DIR / "training_data"
MODEL_OUT    = MODEL3_DIR / "model.pt"
CLASSES_OUT  = MODEL3_DIR / "classes.json"

PHASE1_EPOCHS = 10
PHASE2_EPOCHS = 20
BATCH_SIZE    = 32
PHASE1_LR     = 1e-3
PHASE2_LR     = 1e-4
VAL_SPLIT     = 0.2
SEED          = 42

device = torch.device("mps" if torch.backends.mps.is_available() else
                       "cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

full_dataset = datasets.ImageFolder(DATA_DIR, transform=train_tf)
classes      = full_dataset.classes   # alphabetically sorted list
num_classes  = len(classes)
print(f"Found {len(full_dataset)} images across {num_classes} classes:")
for i, c in enumerate(classes):
    n = sum(1 for _, lbl in full_dataset.samples if lbl == i)
    print(f"  [{i}] {c:<30} {n} images")

# Save classes.json
with open(CLASSES_OUT, "w") as f:
    json.dump({str(i): c for i, c in enumerate(classes)}, f, indent=2)
print(f"\nClasses saved → {CLASSES_OUT}")

# Train / val split
val_size   = int(len(full_dataset) * VAL_SPLIT)
train_size = len(full_dataset) - val_size
generator  = torch.Generator().manual_seed(SEED)
train_ds, val_ds = random_split(full_dataset, [train_size, val_size], generator=generator)

# Apply val transform to val subset
val_ds.dataset = datasets.ImageFolder(DATA_DIR, transform=val_tf)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# Class weights for imbalance
class_counts = np.array([
    sum(1 for _, lbl in full_dataset.samples if lbl == i)
    for i in range(num_classes)
])
weights = 1.0 / class_counts
weights = weights / weights.sum() * num_classes
class_weights = torch.tensor(weights, dtype=torch.float32).to(device)
print(f"\nClass weights: {[f'{w:.2f}' for w in weights]}")

# ---------------------------------------------------------------------------
# Model — ResNet-50, freeze all, replace head
# ---------------------------------------------------------------------------
model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
for p in model.parameters():
    p.requires_grad = False

model.fc = nn.Sequential(   # type: ignore[assignment]
    nn.Dropout(p=0.4),
    nn.Linear(model.fc.in_features, num_classes),  # type: ignore[union-attr]
)
model = model.to(device)

criterion = nn.CrossEntropyLoss(weight=class_weights)


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------
def run_epoch(loader, train: bool, optimizer=None):
    model.train(train)
    total_loss = correct = seen = 0
    with torch.set_grad_enabled(train):
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            out  = model(imgs)
            loss = criterion(out, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * len(imgs)
            correct    += (out.argmax(1) == labels).sum().item()
            seen       += len(imgs)
    return total_loss / seen, correct / seen


def train_phase(label: str, epochs: int, lr: float, params):
    optimizer = torch.optim.Adam(params, lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    best_val  = 0.0

    print(f"\n{'='*55}")
    print(f"  {label}  (lr={lr}, epochs={epochs})")
    print(f"{'='*55}")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        tr_loss, tr_acc = run_epoch(train_loader, train=True,  optimizer=optimizer)
        va_loss, va_acc = run_epoch(val_loader,   train=False)
        scheduler.step()

        marker = ""
        if va_acc > best_val:
            best_val = va_acc
            torch.save(model.state_dict(), MODEL_OUT)
            marker = "  ← saved"

        print(f"  Epoch {epoch:02d}/{epochs}  "
              f"train {tr_acc*100:.1f}%  val {va_acc*100:.1f}%  "
              f"[{time.time()-t0:.0f}s]{marker}")

    return best_val


# ---------------------------------------------------------------------------
# Phase 1 — head only
# ---------------------------------------------------------------------------
best1 = train_phase(
    "Phase 1 — head only",
    PHASE1_EPOCHS,
    PHASE1_LR,
    model.fc.parameters(),
)

# ---------------------------------------------------------------------------
# Phase 2 — unfreeze layer4 + head
# ---------------------------------------------------------------------------
for p in model.layer4.parameters():   # type: ignore[attr-defined]
    p.requires_grad = True

best2 = train_phase(
    "Phase 2 — layer4 + head",
    PHASE2_EPOCHS,
    PHASE2_LR,
    filter(lambda p: p.requires_grad, model.parameters()),
)

print(f"\n{'='*55}")
print(f"  Training complete")
print(f"  Best val acc — Phase 1: {best1*100:.1f}%  Phase 2: {best2*100:.1f}%")
print(f"  Model saved  → {MODEL_OUT}")
print(f"  Classes      → {CLASSES_OUT}")

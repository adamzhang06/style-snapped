import numpy as np
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
import os
import json
from dotenv import load_dotenv, find_dotenv

# --- 1. SETUP & HARDWARE ---
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Training on device: {device}")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "my_vibe_model_2", "synthetic_aesthetics.csv")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "my_vibe_model_2")

# --- 2. DATA PREPARATION ---
print("Loading labels...")
df = pd.read_csv(DATA_PATH)

df_clean = df[df['vibe'] != 'DROP'].copy()
encoder = LabelEncoder()
df_clean['label'] = encoder.fit_transform(df_clean['vibe'])  # type: ignore[assignment]
num_classes = len(encoder.classes_)
print(f"  {len(df_clean)} labeled samples, {num_classes} classes: {list(encoder.classes_)}")

train_df, val_df = train_test_split(df_clean, test_size=0.2, random_state=42, stratify=df_clean['label'])
print(f"  Train: {len(train_df)}, Val: {len(val_df)}")

print("Loading HF dataset and building image index (one-time)...")
hf_dataset = load_dataset("ashraq/fashion-product-images-small", split="train", token=HF_TOKEN)
image_index = {item["id"]: item["image"] for item in hf_dataset}  # type: ignore[index]
print(f"  Indexed {len(image_index)} images")

# Augmented transform for training; clean transform for validation
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

class VibeDataset(Dataset):
    def __init__(self, dataframe, image_index, transform):
        self.dataframe = dataframe.reset_index(drop=True)
        self.image_index = image_index
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        image = self.image_index[int(row['image_id'])].convert("RGB")
        return self.transform(image), int(row['label'])

# num_workers=0 required for MPS
train_loader = DataLoader(VibeDataset(train_df, image_index, train_transform), batch_size=32, shuffle=True, num_workers=0)
val_loader = DataLoader(VibeDataset(val_df, image_index, val_transform), batch_size=32, shuffle=False, num_workers=0)

# --- 3. MODEL ARCHITECTURE ---
print(f"\nInitializing ResNet-50 for {num_classes} classes...")
model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

for param in model.parameters():
    param.requires_grad = False
for param in model.layer4.parameters():
    param.requires_grad = True

in_features = model.fc.in_features
# Dropout before the head to regularize — this is the main overfitting fix
model.fc = nn.Sequential(  # type: ignore[assignment]
    nn.Dropout(p=0.4),
    nn.Linear(in_features, num_classes),
)
model = model.to(device)

# Weighted loss so tail classes aren't ignored
label_counts = df_clean['label'].value_counts().sort_index()
class_weights: np.ndarray = (1.0 / label_counts).to_numpy(dtype=float)
class_weights = class_weights / class_weights.sum() * num_classes
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)

# layer4 at 10x lower LR than the head; weight_decay regularizes both
optimizer = optim.Adam([
    {"params": model.layer4.parameters(), "lr": 1e-4, "weight_decay": 1e-4},
    {"params": model.fc.parameters(),     "lr": 1e-3, "weight_decay": 1e-4},
])

# --- 4. TRAINING LOOP WITH BEST-CHECKPOINT SAVING ---
epochs = 30
best_val_acc = 0.0
best_epoch = 0
model_path = os.path.join(OUTPUT_DIR, "resnet50_vibe.pt")
print(f"\nStarting training ({epochs} epochs, saving best checkpoint)...")

for epoch in range(epochs):
    # Train
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [train]")
    for images, labels in progress_bar:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        progress_bar.set_postfix(loss=f"{loss.item():.3f}", acc=f"{100.*correct/total:.1f}%")

    train_acc = 100. * correct / total
    train_loss = running_loss / len(train_loader)

    # Validate
    model.eval()
    val_correct = 0
    val_total = 0
    val_loss = 0.0
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [val]  ", leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    val_acc = 100. * val_correct / val_total
    val_loss /= len(val_loader)

    marker = ""
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_epoch = epoch + 1
        torch.save(model.state_dict(), model_path)
        marker = "  ✓ saved"

    print(f"  Epoch {epoch+1:2d}: train_loss={train_loss:.3f} train_acc={train_acc:.1f}%  val_loss={val_loss:.3f} val_acc={val_acc:.1f}%{marker}")

# --- 5. SAVE LABEL CLASSES ---
labels_path = os.path.join(OUTPUT_DIR, "label_classes.json")
with open(labels_path, "w") as f:
    json.dump(list(encoder.classes_), f, indent=2)

print(f"\nBest val accuracy: {best_val_acc:.1f}% at epoch {best_epoch}")
print(f"Model saved to {model_path}")
print(f"Label classes saved to {labels_path}")
print("Training complete!")

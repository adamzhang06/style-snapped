"""
Script 1: Embed 5,000 fashion images with a headless ResNet-50, cluster with
KMeans (k=50), and identify the 3 centroid-nearest images per cluster.

Outputs (written to backend/my_vibe_model_3/):
  cluster_assignments.csv  — every image with its cluster_id, centroid rank,
                             and distance to the cluster centre
  embeddings.npy           — (5000, 2048) float32 matrix (re-usable cache)
"""

import os
import json
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torchvision import models, transforms
from datasets import load_dataset
from sklearn.cluster import KMeans
from PIL import Image
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH   = os.path.join(SCRIPT_DIR, "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)

HF_TOKEN   = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found — add it to backend/scripts/.env")

OUTPUT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "2_my_vibe_model"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

EMBEDDINGS_PATH    = os.path.join(OUTPUT_DIR, "embeddings.npy")
ASSIGNMENTS_PATH   = os.path.join(OUTPUT_DIR, "cluster_assignments.csv")
IMAGE_IDS_PATH     = os.path.join(OUTPUT_DIR, "image_ids.json")

N_CLUSTERS         = 100
CENTROIDS_PER_CLUSTER = 3
BATCH_SIZE         = 64

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"[1/5] Using device: {device}")

# ---------------------------------------------------------------------------
# Step 1 — Load dataset
# ---------------------------------------------------------------------------
print("[2/5] Loading HuggingFace dataset...")
dataset = load_dataset(
    "ashraq/fashion-product-images-small",
    split="train",
    token=HF_TOKEN,
)
N = len(dataset)
print(f"      Loaded {N} images.")

# ---------------------------------------------------------------------------
# Step 2 — Build headless ResNet-50 feature extractor
# ---------------------------------------------------------------------------
print("[3/5] Building headless ResNet-50...")
backbone = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
backbone.fc = nn.Identity()   # strip classifier → 2048-dim output
backbone = backbone.to(device)
backbone.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# ---------------------------------------------------------------------------
# Step 3 — Extract embeddings (with checkpoint resume)
# ---------------------------------------------------------------------------
if os.path.exists(EMBEDDINGS_PATH) and os.path.exists(IMAGE_IDS_PATH):
    print(f"      Found cached embeddings at {EMBEDDINGS_PATH} — loading.")
    embeddings = np.load(EMBEDDINGS_PATH)
    with open(IMAGE_IDS_PATH) as f:
        image_ids = json.load(f)
    print(f"      Loaded {len(image_ids)} cached embeddings.")
else:
    print(f"[3/5] Extracting {N} embeddings in batches of {BATCH_SIZE}...")
    embeddings = np.zeros((N, 2048), dtype=np.float32)
    image_ids  = []

    t0 = time.time()
    with torch.no_grad():
        for batch_start in range(0, N, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, N)
            batch_items = [dataset[i] for i in range(batch_start, batch_end)]

            tensors = []
            for item in batch_items:
                img = item["image"]
                if img.mode != "RGB":
                    img = img.convert("RGB")
                tensors.append(transform(img))
                image_ids.append(item["id"])

            batch_tensor = torch.stack(tensors).to(device)
            feats = backbone(batch_tensor)            # (B, 2048)
            embeddings[batch_start:batch_end] = feats.cpu().numpy()

            if (batch_start // BATCH_SIZE) % 10 == 0:
                elapsed = time.time() - t0
                pct = batch_end / N * 100
                print(f"      {batch_end}/{N} images embedded ({pct:.1f}%)  "
                      f"[{elapsed:.0f}s elapsed]")

    np.save(EMBEDDINGS_PATH, embeddings)
    with open(IMAGE_IDS_PATH, "w") as f:
        json.dump(image_ids, f)
    print(f"      Embeddings saved to {EMBEDDINGS_PATH}")

# ---------------------------------------------------------------------------
# Step 4 — KMeans clustering
# ---------------------------------------------------------------------------
print(f"[4/5] Running KMeans with {N_CLUSTERS} clusters on {len(image_ids)} vectors...")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10, verbose=0)
kmeans.fit(embeddings)
cluster_labels = kmeans.labels_          # shape (N,)
centers        = kmeans.cluster_centers_ # shape (50, 2048)
print(f"      Clustering done. Inertia: {kmeans.inertia_:.2f}")

# ---------------------------------------------------------------------------
# Step 5 — Find 3 centroid-nearest images per cluster
# ---------------------------------------------------------------------------
print(f"[5/5] Finding {CENTROIDS_PER_CLUSTER} centroid-nearest images per cluster...")

# Pre-build per-cluster index lists for speed
cluster_member_idx = [[] for _ in range(N_CLUSTERS)]
for idx, cid in enumerate(cluster_labels):
    cluster_member_idx[cid].append(idx)

records = []
for cid in range(N_CLUSTERS):
    idxs   = np.array(cluster_member_idx[cid])
    vecs   = embeddings[idxs]               # (M, 2048)
    center = centers[cid]                   # (2048,)

    # Euclidean distance from each member to the cluster centroid
    diffs  = vecs - center                  # (M, 2048)
    dists  = np.linalg.norm(diffs, axis=1)  # (M,)

    # Argsort ascending — closest first
    order  = np.argsort(dists)
    top_k  = min(CENTROIDS_PER_CLUSTER, len(order))

    for rank, pos in enumerate(order):
        global_idx    = idxs[pos]
        centroid_rank = rank + 1 if rank < top_k else 0
        records.append({
            "image_id":     image_ids[global_idx],
            "cluster_id":   int(cid),
            "dist_to_center": float(dists[pos]),
            "centroid_rank":  int(centroid_rank) if rank < top_k else 0,
            "is_centroid":    int(rank < top_k),
        })

    # Non-centroid members — add them with rank 0
    for rank, pos in enumerate(order[top_k:], start=top_k):
        global_idx = idxs[pos]
        records.append({
            "image_id":     image_ids[global_idx],
            "cluster_id":   int(cid),
            "dist_to_center": float(dists[pos]),
            "centroid_rank":  0,
            "is_centroid":    0,
        })

df = pd.DataFrame(records)
df.to_csv(ASSIGNMENTS_PATH, index=False)

centroid_count = df["is_centroid"].sum()
print(f"\nDone. {centroid_count} centroid images across {N_CLUSTERS} clusters.")
print(f"Cluster assignments saved → {ASSIGNMENTS_PATH}")
print(f"Embeddings cached        → {EMBEDDINGS_PATH}")
print("\nNext step: run  2_vlm_label_propagation.py")

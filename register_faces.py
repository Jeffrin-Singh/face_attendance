import cv2
import os
import pickle
import numpy as np
from insightface.app import FaceAnalysis

DATASET = "dataset"
MIN_IMAGES = 5

app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

db = {}

for person in os.listdir(DATASET):
    path = os.path.join(DATASET, person)
    if not os.path.isdir(path):
        continue

    embs = []
    for img_name in os.listdir(path):
        img = cv2.imread(os.path.join(path, img_name))
        if img is None:
            continue

        faces = app.get(img)
        if not faces:
            continue

        face = max(faces, key=lambda f: f.area)
        emb = face.embedding
        emb = emb / np.linalg.norm(emb)
        embs.append(emb)

    if len(embs) < MIN_IMAGES:
        print(f"Skipped {person} (not enough faces)")
        continue

    mean_emb = np.mean(embs, axis=0)
    mean_emb = mean_emb / np.linalg.norm(mean_emb)
    db[person] = mean_emb
    print(f"Registered {person}")

with open("embeddings.pkl", "wb") as f:
    pickle.dump(db, f)

print("embeddings.pkl saved")

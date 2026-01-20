import cv2
import os
from insightface.app import FaceAnalysis

# ================== USER INPUT ==================
name = input("Enter person name: ").strip()
if not name:
    print("❌ Name required")
    exit()

SAVE_DIR = f"dataset/{name}"
TOTAL = 25
os.makedirs(SAVE_DIR, exist_ok=True)

# ================== LOAD INSIGHTFACE ==================
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

# ================== CAMERA ==================
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Camera error")
    exit()

count = 0
print("\n📸 Capturing faces (saving FULL FRAME)...")
print("➡️ Sit straight, good lighting")
print("➡️ Slight head movement\n")

while count < TOTAL:
    ret, frame = cap.read()
    if not ret:
        continue

    # Only check if a face exists (DO NOT CROP)
    faces = app.get(frame)
    if not faces:
        continue

    # 🔥 SAVE FULL FRAME (IMPORTANT)
    cv2.imwrite(f"{SAVE_DIR}/{count+1}.jpg", frame)
    count += 1
    print(f"Saved {count}/{TOTAL}")

cap.release()
print("\n✅ Face capture completed successfully")
print(f"📁 Images saved in '{SAVE_DIR}'")
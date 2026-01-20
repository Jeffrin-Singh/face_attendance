import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis

def cosine(a, b):
    return np.dot(a, b)

app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0)

with open("embeddings.pkl", "rb") as f:
    db = pickle.load(f)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    faces = app.get(frame)
    for face in faces:
        emb = face.embedding
        emb = emb / np.linalg.norm(emb)

        name = "Unknown"
        score_max = 0
        for k, v in db.items():
            s = cosine(emb, v)
            if s > score_max:
                score_max = s
                name = k

        if score_max < 0.55:
            name = "Unknown"

        x1, y1, x2, y2 = map(int, face.bbox)
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
        cv2.putText(frame, f"{name} {score_max:.2f}",
                    (x1,y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

    cv2.imshow("Recognition Test", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

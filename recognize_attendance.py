import cv2, csv, os, pickle, time
import numpy as np
from datetime import datetime
from insightface.app import FaceAnalysis
from collections import deque, Counter

THRESHOLD = 0.55

def cosine(a, b):
    return np.dot(a, b)

app_face = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app_face.prepare(ctx_id=0)

with open("embeddings.pkl", "rb") as f:
    db = pickle.load(f)

cam = None
camera_active = True
current_user = None
popup = None
history = deque(maxlen=5)

def set_current_user(u):
    global current_user
    current_user = u

def set_camera_state(s):
    global camera_active
    camera_active = s

def stable(name):
    history.append(name)
    c = Counter(history).most_common(1)[0]
    return c[0] if c[1] >= 3 else "Unknown"

def mark_attendance(name):
    global popup
    if not current_user:
        return

    file = f"attendance_{current_user}.csv"
    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%I:%M:%S %p")

    if not os.path.exists(file):
        with open(file,"w",newline="") as f:
            csv.writer(f).writerow(["Name","Date","Time"])

    with open(file,"r+",newline="") as f:
        lines = f.readlines()
        if any(name in l and today in l for l in lines):
            popup = f"{name} already marked"
            return

        csv.writer(f).writerow([name,today,time_now])
        popup = f"Attendance marked for {name}"

def generate_frames():
    global cam
    if cam is None:
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(0.5)

    while True:
        if not camera_active:
            time.sleep(0.2)
            continue

        ret, frame = cam.read()
        if not ret:
            continue

        faces = app_face.get(frame)
        for face in faces:
            emb = face.embedding
            emb = emb / np.linalg.norm(emb)

            name, best = "Unknown", 0
            for k,v in db.items():
                s = cosine(emb,v)
                if s > best:
                    best = s
                    name = k

            if best < THRESHOLD:
                name = "Unknown"

            name = stable(name)
            if name != "Unknown":
                mark_attendance(name)

            x1,y1,x2,y2 = map(int, face.bbox)
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            cv2.putText(frame,name,(x1,y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2)

        _, buf = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
               + buf.tobytes() + b"\r\n")

def get_popup_message():
    global popup
    msg = popup
    popup = None
    return msg

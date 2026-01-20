from flask import Flask, render_template, request, redirect, session, Response, send_file
import os, hashlib, csv
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


from recognize_attendance import (
    generate_frames,
    set_current_user,
    set_camera_state,
    get_popup_message
)

app = Flask(__name__)
app.secret_key = "face_attendance"


# ================= PASSWORD HASH =================
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_pw(request.form["password"])

        if not os.path.exists("users.csv"):
            return "No users found"

        with open("users.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == username and row[1] == password:
                    session["user"] = username
                    session["role"] = row[2]   # 🔥 store role
                    set_current_user(username)
                    set_camera_state(True)

                    if row[2] == "admin":
                        return redirect("/admin")
                    else:
                        return redirect("/dashboard")

        return "Invalid login"

    return render_template("login.html")


@app.route("/admin")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/")

    users = []

    with open("users.csv", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[2] == "user":
                users.append(row[0])

    return render_template("admin_dashboard.html", users=users)


@app.route("/admin/user/<username>")
def admin_view_user(username):
    if session.get("role") != "admin":
        return redirect("/")

    file = f"attendance_{username}.csv"
    data = []

    if os.path.exists(file):
        with open(file, newline="") as f:
            reader = csv.reader(f)
            data = list(reader)

    return render_template(
        "admin_user_attendance.html",
        username=username,
        data=data
    )


@app.route("/admin/download/<username>/<fmt>")
def admin_download(username, fmt):
    if session.get("role") != "admin":
        return redirect("/")

    csv_file = f"attendance_{username}.csv"
    if not os.path.exists(csv_file):
        return "No data"

    if fmt == "excel":
        df = pd.read_csv(csv_file)
        file = f"attendance_{username}.xlsx"
        df.to_excel(file, index=False)
        return send_file(file, as_attachment=True)

    if fmt == "pdf":
        df = pd.read_csv(csv_file)
        file = f"attendance_{username}.pdf"
        doc = SimpleDocTemplate(file)
        table = Table([df.columns.tolist()] + df.values.tolist())
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 1, colors.black)
        ]))
        doc.build([table])
        return send_file(file, as_attachment=True)


# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_pw(request.form["password"])

        # create users.csv if not exists
        if not os.path.exists("users.csv"):
            with open("users.csv", "w", newline="") as f:
                pass

        # check if user already exists
        with open("users.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == username:
                    # 🔥 user exists → redirect to login
                    return redirect("/?exists=1")

        # default role = user
        with open("users.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([username, password, "user"])

        # after successful signup → go to login
        return redirect("/?signup=1")

    return render_template("signup.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", username=session["user"])


# ================= VIDEO STREAM =================
@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ================= POPUP =================
@app.route("/popup")
def popup():
    return get_popup_message() or ""



# ================= LOGOUT =================
@app.route("/logout")
def logout():
    set_camera_state(False)
    session.clear()
    return redirect("/")

@app.route("/download_pdf")
def download_pdf():
    if "user" not in session:
        return redirect("/")

    username = session["user"]
    csv_file = f"attendance_{username}.csv"

    if not os.path.exists(csv_file):
        return "No attendance data found"

    # Load CSV
    df = pd.read_csv(csv_file)

    pdf_file = f"attendance_{username}.pdf"

    # Create PDF
    doc = SimpleDocTemplate(pdf_file)
    table_data = [df.columns.tolist()] + df.values.tolist()

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    doc.build([table])

    return send_file(pdf_file, as_attachment=True)



# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

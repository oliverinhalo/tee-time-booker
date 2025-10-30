import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, redirect, flash
import tee_time_booker  # your booking logic module

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/booking")
def booking():
    load_dotenv()
    club = os.getenv("CLUB_NAME")
    username = os.getenv("BRS_USERNAME")
    password = os.getenv("BRS_PASSWORD")
    players = os.getenv("PLAYERS", ",").split(",")



    return render_template("booking.html", club=club, players=players)


@app.route("/", methods=["GET", "POST"])
def index():
    load_dotenv()

    # If environment variables already exist, go straight to booking
    if all(os.getenv(k) for k in ("BRS_USERNAME", "BRS_PASSWORD", "CLUB_NAME")):
        return redirect(url_for("booking"))

    # Handle login form submission
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        club = request.form.get("club", "").strip()

        if not username or not password or not club:
            flash("All fields are required.", "error")
            return render_template("login.html")

        # Save credentials to .env file
        with open(".env", "w") as f:
            f.write(f"BRS_USERNAME={username}\n")
            f.write(f"BRS_PASSWORD={password}\n")
            f.write(f"CLUB_NAME={club}\n")

        flash("Login successful!", "success")
        return redirect(url_for("booking"))

    # If GET and no saved credentials, show login page
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)

import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, redirect, flash
import tee_time_booker

app = Flask(__name__)
app.secret_key = os.urandom(24)

def update_env_players(players):
    lines = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        if line.startswith("PLAYERS="):
            new_lines.append(f"PLAYERS={','.join(players)}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"PLAYERS={','.join(players)}\n")

    with open(".env", "w") as f:
        f.writelines(new_lines)


@app.route("/booking", methods=["GET", "POST"])
def booking():
    load_dotenv(override=True)  # <<< force refresh
    club = os.getenv("CLUB_NAME")
    username = os.getenv("BRS_USERNAME")
    password = os.getenv("BRS_PASSWORD")
    players = os.getenv("PLAYERS", "")
    players = players.split(",") if players else []

    if request.method == "POST":
        # Add player form
        if "player" in request.form:
            new_player = request.form.get("player", "").strip()
            if new_player:
                if new_player not in players:
                    players.append(new_player)
                    update_env_players(players)
                    flash(f"Added player: {new_player}", "success")
                else:
                    flash("Player already exists.", "warning")
            else:
                flash("Player name cannot be empty.", "error")
            return redirect(url_for("booking"))

        # Remove player form
        if "remove_player" in request.form:
            player_to_remove = request.form.get("remove_player", "").strip()
            if player_to_remove in players:
                players.remove(player_to_remove)
                update_env_players(players)
                flash(f"Removed player: {player_to_remove}", "success")
            else:
                flash("Player not found.", "error")
            return redirect(url_for("booking"))

        # Booking form
        date_str = request.form.get("date")
        time = [request.form.get("time")]
        selected_players = request.form.getlist("selected_players")

        # Validate date is in the future
        from datetime import datetime, date
        try:
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = date.today()
            if booking_date <= today:
                flash("You can only book for future dates.", "error")
                return redirect(url_for("booking"))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("booking"))

        # Convert date format for the booking system
        date = date_str.replace("-", "/")

        if len(selected_players) < 1 or len(selected_players) > 4:
            flash("Please select between 1 and 4 players.", "error")
            return redirect(url_for("booking"))

        #result = tee_time_booker.run(username, password, club, time, date, *selected_players)
        flash("Booking submitted.", "success")
        return redirect(url_for("booking"))

    load_dotenv(override=True)  # <<< force reload after changes
    players = os.getenv("PLAYERS", "")
    players = players.split(",") if players else []

    return render_template("booking.html", club=club, players=players)


@app.route("/", methods=["GET", "POST"])
def index():
    load_dotenv(override=True)
    if all(os.getenv(k) for k in ("BRS_USERNAME", "BRS_PASSWORD", "CLUB_NAME")):
        return redirect(url_for("booking"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        club = request.form.get("club", "").strip()

        if not username or not password or not club:
            flash("All fields are required.", "error")
            return render_template("login.html")

        with open(".env", "w") as f:
            f.write(f"BRS_USERNAME={username}\n")
            f.write(f"BRS_PASSWORD={password}\n")
            f.write(f"CLUB_NAME={club}\n")

        flash("Login successful!", "success")
        return redirect(url_for("booking"))

    return render_template("login.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)

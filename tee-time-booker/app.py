import os
import signal
import sys
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, redirect, flash
import DB
import rsa

# Create database instance
DB = DB.Database()

# Function to handle graceful shutdown
def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    sys.exit(0)

# Register signal handlers only if running as main
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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

        # Delete booking form
        if "delete_booking" in request.form:
            booking_id = request.form.get("delete_booking")
            try:
                result = DB.execute_update("DELETE FROM bookings WHERE id = ?", (booking_id,))
                if result > 0:
                    flash("Booking deleted successfully.", "success")
                else:
                    flash("Booking not found.", "error")
            except Exception as e:
                flash(f"Error deleting booking: {str(e)}", "error")
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
        publicKey, privateKey = rsa.newkeys(512)
        DB.execute_update("INSERT INTO bookings (username, club, date, time, players, password, private_key) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, club, date, time[0], ",".join(selected_players), rsa.encrypt(password.encode(), publicKey).hex(), privateKey.save_pkcs1().decode('utf-8')))


        flash("Booking submitted.", "success")
        return redirect(url_for("booking"))

    load_dotenv(override=True)  # <<< force reload after changes
    players = os.getenv("PLAYERS", "")
    players = players.split(",") if players else []

    # Get current bookings from database
    try:
        current_bookings = DB.execute_query("SELECT * FROM bookings ORDER BY date ASC, time ASC")
        # Format the bookings for display
        for booking in current_bookings:
            # Convert date format from YYYY/MM/DD to DD/MM/YYYY for display
            try:
                from datetime import datetime
                date_obj = datetime.strptime(booking['date'], "%Y/%m/%d")
                booking['formatted_date'] = date_obj.strftime("%d/%m/%Y")
                booking['day_name'] = date_obj.strftime("%A")
            except:
                booking['formatted_date'] = booking['date']
                booking['day_name'] = ''
            
            # Format players list
            booking['players_list'] = booking['players'].split(',') if booking['players'] else []
    except Exception as e:
        current_bookings = []
        flash(f"Error loading bookings: {str(e)}", "error")

    return render_template("booking.html", club=club, players=players, current_bookings=current_bookings)


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
    try:
        print("Starting Flask application...")
        app.run(debug=True, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    finally:
        print("Cleaning up...")
        sys.exit(0)

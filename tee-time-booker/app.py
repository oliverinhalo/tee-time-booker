import os
from dotenv import load_dotenv
from flask import Flask, render_template
import tee_time_booker

app = Flask(__name__)


@app.route("/booking")
def booking():
    return render_template("booking.html", club=club)


@app.route("/", methods=["POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        club = request.form.get("club")
        
        with open(".env", "w") as f:
            f.write(f"BRS_USERNAME={username}\nBRS_PASSWORD={password}\nCLUB_NAME={club}")

        return redirect(url_for("booking"))

    try:
        load_dotenv()
    
        username = os.environ['BRS_USERNAME']
        password = os.environ['BRS_PASSWORD']
        club = os.environ['CLUB_NAME']

        return redirect(url_for("booking"))

    except:
        return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)

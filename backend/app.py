from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    session,
    redirect
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import requests
import os


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "templates")
)

STATIC_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "static")
)


# ============================================================
# DEBUG INFORMATION
# ============================================================

print("========================================")
print("BASE_DIR:", BASE_DIR)
print("TEMPLATE_DIR:", TEMPLATE_DIR)
print("STATIC_DIR:", STATIC_DIR)
print("Template folder exists:", os.path.exists(TEMPLATE_DIR))
print("Static folder exists:", os.path.exists(STATIC_DIR))
print(
    "index.html exists:",
    os.path.exists(os.path.join(TEMPLATE_DIR, "index.html"))
)
print("========================================")


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "smart-farming-development-key"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_PATH = r"D:\SmartFarmingData\smart_farming.db"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DATABASE_PATH.replace(chr(92), '/')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    soil_type = db.Column(db.String(100))
    season = db.Column(db.String(100))
    location = db.Column(db.String(100))


# ============================================================
# WEATHER API KEY
# ============================================================

WEATHER_API_KEY = "ca785a1a4b00323cbfc504dabe03306c"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    print("SESSION:", dict(session))

    return render_template(
        "index.html"
    )


# ============================================================
# CROP PAGE
# ============================================================

@app.route("/crop")
def crop():

    return render_template(
        "pages/crop.html"
    )


# ============================================================
# WEATHER PAGE
# ============================================================

@app.route("/weather")
def weather():

    return render_template(
        "pages/weather.html"
    )


# ============================================================
# DISEASE PAGE
# ============================================================

@app.route("/disease")
def disease():

    return render_template(
        "pages/disease.html"
    )


# ============================================================
# MARKET PAGE
# ============================================================

@app.route("/market")
def market():

    return render_template(
        "pages/market.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # --------------------------------------------------------
    # GET REQUEST
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "pages/login.html"
        )


    # --------------------------------------------------------
    # POST REQUEST
    # --------------------------------------------------------

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    user = User.query.filter_by(
        email=email
    ).first()


    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if user and user.check_password(password):

        # Clear any old session data
        session.clear()

        # Store logged-in user
        session["user_id"] = user.id
        session["user_name"] = user.name

        print(
            "LOGIN SUCCESS:",
            dict(session)
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        })


    # --------------------------------------------------------
    # INVALID LOGIN
    # --------------------------------------------------------

    print(
        "LOGIN FAILED FOR:",
        email
    )

    return jsonify({
        "success": False,
        "message": "Invalid email or password"
    }), 401


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    print(
        "LOGOUT BEFORE:",
        dict(session)
    )

    session.clear()

    print(
        "LOGOUT AFTER:",
        dict(session)
    )

    return redirect("/")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    # --------------------------------------------------------
    # VALIDATE INPUT
    # --------------------------------------------------------

    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400


    # --------------------------------------------------------
    # CHECK EXISTING USER
    # --------------------------------------------------------

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        return jsonify({
            "success": False,
            "message": "An account with this email already exists"
        }), 409


    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    user = User(
        name=name,
        email=email
    )

    user.set_password(
        password
    )


    # --------------------------------------------------------
    # SAVE USER
    # --------------------------------------------------------

    db.session.add(user)

    db.session.commit()


    print(
        "NEW USER CREATED:",
        user.id,
        user.email
    )


    return jsonify({
        "success": True,
        "message": "Account created successfully"
    }), 201


# ============================================================
# SERVICE WORKER
# ============================================================

@app.route("/sw.js")
def service_worker():

    return send_from_directory(
        STATIC_DIR,
        "sw.js",
        mimetype="application/javascript"
    )


# ============================================================
# MANIFEST
# ============================================================

@app.route("/manifest.json")
def manifest():

    return send_from_directory(
        STATIC_DIR,
        "manifest.json",
        mimetype="application/json"
    )


# ============================================================
# WEATHER API
# ============================================================

@app.route("/api/weather")
def get_weather():

    city = request.args.get(
        "city",
        "Delhi"
    )


    # --------------------------------------------------------
    # CHECK API KEY
    # --------------------------------------------------------

    if not WEATHER_API_KEY:

        return jsonify({
            "error": "WEATHER_API_KEY environment variable is not set"
        }), 500


    # --------------------------------------------------------
    # OPENWEATHER URL
    # --------------------------------------------------------

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city},IN"
        f"&appid={WEATHER_API_KEY}"
        "&units=metric"
        "&cnt=40"
    )


    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()


        # ----------------------------------------------------
        # CHECK API RESPONSE
        # ----------------------------------------------------

        if data.get("cod") != "200":

            return jsonify({
                "error": "City not found"
            }), 404


        # ----------------------------------------------------
        # CURRENT WEATHER
        # ----------------------------------------------------

        current = data["list"][0]


        # ----------------------------------------------------
        # FORECAST
        # ----------------------------------------------------

        forecast = []

        seen_dates = []


        for item in data["list"]:

            date = item["dt_txt"].split(" ")[0]


            if (
                date not in seen_dates
                and len(forecast) < 5
            ):

                seen_dates.append(
                    date
                )

                forecast.append({

                    "date": date,

                    "temp": round(
                        item["main"]["temp"]
                    ),

                    "desc": item["weather"][0][
                        "description"
                    ].title(),

                    "rain": round(
                        item.get("pop", 0) * 100
                    )
                })


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result = {

            "city": data["city"]["name"],

            "country": data["city"]["country"],

            "temp": round(
                current["main"]["temp"]
            ),

            "feels_like": round(
                current["main"]["feels_like"]
            ),

            "desc": current["weather"][0][
                "description"
            ].title(),

            "humidity": current["main"]["humidity"],

            "wind": round(
                current["wind"]["speed"] * 3.6
            ),

            "rain": round(
                current.get("pop", 0) * 100
            ),

            "forecast": forecast
        }


        return jsonify(
            result
        )


    # --------------------------------------------------------
    # REQUEST ERROR
    # --------------------------------------------------------

    except requests.exceptions.RequestException as e:

        return jsonify({
            "error": f"Weather API request failed: {str(e)}"
        }), 500


    # --------------------------------------------------------
    # OTHER ERROR
    # --------------------------------------------------------

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
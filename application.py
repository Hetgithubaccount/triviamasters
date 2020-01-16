import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///trivia.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # Check if confirmation and password are the same, if  password is filled in and if username is filled in, if not return apology
        if confirmation != password:
            return apology("verkeerd wachtwoord", 400)
        elif not password:
            return apology("must provide password", 400)
        elif not username:
            return apology("must provide username", 400)
        # Query in users for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        # If username already exists return apology
        if len(rows) != 0:
            return apology("username already exists", 400)
        # Make a hash of the password
        hashe = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        # Insert username and hash in the database
        db.execute("INSERT INTO users (username, hash) values (:username,:hash)", username=username, hash=hashe)
        # Return to login page
        return render_template("home_user")
    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("register.html")

@app.route("/start", methods =["GET", "POST"])
def start():
    print("test")

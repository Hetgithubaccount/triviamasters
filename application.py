import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import random
import sqlite3
import csv
import requests

from helpers import apology, login_required
import json

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

games = list()
singlegameplayers = dict()
import csv
import time
db = SQL("sqlite:///trivia.db")


print()

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # checks if username is filled in
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # checks if password was filled in
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # checks if passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password doesn't match", 400)

        result = db.execute("SELECT * FROM users \
                            WHERE username=:username", username=request.form.get("username"))

        if result:
            return apology("Username already exist", 400)

        #creates user
        session["user_id"] = db.execute("INSERT INTO users (username, hash) \
                             VALUES(:username, :hash)", \
                             username=request.form.get("username"), \
                             hash=generate_password_hash(request.form.get("password")))

        return render_template("userpage.html")

    else:
        return render_template("register.html")

@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    result = db.execute("SELECT * FROM users \
                            WHERE username=:username", username=request.args.get("username"))
    if len(result) > 0:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("userpage.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/friends", methods=["GET", "POST"])
def findfriends():
    if request.method == "GET":
        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        for i in username:
            for name in i:
                username = i[name]
        ownfriends = db.execute("SELECT * FROM friends WHERE username = :username", username = username)
        reversefriends = db.execute("SELECT * FROM friends WHERE friend = :friend", friend = username)
        # Wisselt volgorde in lijst, zodat vriend wordt getoond op pagina ipv jouw eigen naam
        for i in reversefriends:
            dude = i["username"]
            i["username"] = i["friend"]
            i["friend"] = dude
        portfolio_contents = ownfriends + reversefriends
        return render_template("friends.html", portfolio_contents = portfolio_contents)
    else:
        return render_template("friends.html")

@app.route("/addfriend", methods=["GET", "POST"])
def addfriend():
    if request.method == "POST":
        friendname = request.form.get("addusername")

        # Checks if username is legit
        result = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("addusername"))
        if not result:
            return apology("user does not exist", 403)

        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        for i in username:
            for name in i:
                username = i[name]
        db.execute("INSERT INTO friends (username, friend, games, won, lose) VALUES (:username, :friend, :games, :won, :lose)", username = username,
                                                                                                friend = friendname, games = 0, won = 0, lose = 0)
        return redirect("/friends")
    else:
        return render_template("friends.html")

@app.route("/delfriend", methods=["GET", "POST"])
def delfriend():
    if request.method == "POST":
        friendname = request.form.get("delusername")

        # Checks if username is legit
        result = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("delusername"))
        if not result:
            return apology("user does not exist", 403)

        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        for i in username:
            for name in i:
                username = i[name]
        db.execute("DELETE FROM friends WHERE username = :username and friend = :friendname", username = username, friendname = friendname)

        return redirect("/friends")
    else:
        return render_template("friends.html")

@app.route("/", methods=["GET", "POST"])
def start():
    session["score"] = 0
    session["vraag"] = 0
    if request.method == "POST":
        if request.form.get("singleplayer"):
            return render_template("game.html")
        elif not request.form.get("username") and not request.form.get("opponent"):
            return apology("must provide username", 403)
        elif request.form.get("opponent") and not request.form.get("number"):
            return apology("must provide code", 403)
        elif request.form.get("username"):
            newgame = True
            while newgame:
                code = random.randrange(100000, 999999)
                result = db.execute("SELECT * FROM spel WHERE spelid=:code", code=code)
                if not result:
                    db.execute("INSERT INTO spel (spelid, username, ronde) VALUES (:spelid, :username, :ronde", spelid=code, username=request.form.get("username"), ronde=1)
                    session["gameid"] = code
                    return render_template("wacht.html", code=code, username=request.form.get("username"))


    else:
        return render_template("index.html")

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.form.get("opponent") and request.form.get("number"):
        code = request.form.get("number")
        result = db.execute("SELECT * FROM spel WHERE gameid=:gameid", gameid=code)
        if result:
            db.execute("UPDATE spel SET opponent=:opponent WHERE gameid=:code", opponent=request.form.get("opponent"), code=code)
            return render_template("game.html")
        else:
            return apology("enter valid code", 403)
    else:
        return render_template("index.html")

@app.route("/wacht", methods=["GET", "POST"])
def wacht():
    opponent = None
    while opponent == None:
        result = db.execute("SELECT opponent FROM spel WHERE gameid:=gameid", gameid=session["gameid"])
        if result:
            return render_template("game.html")

        time.sleep(10)

    return render_template("wacht.html")

@app.route("/game", methods=["GET", "POST"])
def startsinglegame():
    if request.method == "GET":
        quest = newquestion()
        question = quest[0]
        coranswer = quest[1]
        answerlist = quest[2]
        categ = quest[3]
        session["coranswer"] = coranswer
        return render_template("game.html", question=question, answerlist=answerlist, coranswer=coranswer, categ = categ)

    if request.method == "POST":
        ingevuld = str(request.form.get("answer"))
        if ingevuld == session["coranswer"]:
            session["score"] += 1
            print("goed")
        session["vraag"] += 1
        # print(vraag)
        if session["vraag"] == 10:
            session["vraag"] = 0
            return render_template("eind.html")
        print(session["score"])
        # print(vraag)

        return redirect("/game")


def newquestion():
    with open('questions.csv', newline='') as csv_file:
            reader = list(csv.reader(csv_file))    # nieuwe vraag
            sequence = random.choice(reader)
            category = sequence[0]
            question = sequence[3]
            coranswer = sequence[4]
            # print(coranswer)
            answerlist = {sequence[4], sequence[5], sequence[6], sequence[7]}
            # print("test", [question, coranswer, answerlist, category])
    return [question, coranswer, answerlist, category]

def vragen():
    response = requests.get("https://opentdb.com/api.php?amount=49&category=21&type=multiple")
    sport = response.json()

@app.route("/eind", methods=["GET", "POST"])
def eind():
    if request.method == "POST":
        session.clear()
        return redirect("/")
    else:
        return render_template("eind.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


@app.route("/userpage", methods=["GET", "POST"])
@login_required
def userpage():
    if request.method == "POST":
        return redirect("game.html")
    else:
        return render_template("userpage.html")

@app.route("/play", methods=["GET", "POST"])
@login_required
def gamewfriend():
    session["score"] = 0
    session["vraag"] = 0
    if request.method == "POST":
        print("hi")
        opponent = request.form.get("f-opponent")
        if not opponent:
             return apology("must insert friends username", 403)
        id = session["user_id"]
        username = db.execute("SELECT username FROM users WHERE id = :id", id=id)
        for i in username:
            for name in i:
                username = i[name]
        print(username)
        friend = db.execute("SELECT friend FROM friends WHERE username = :username",
                          username=username)
        if not friend:
             print("hi")
             return apology("must add opponent as friend", 403)
        ronde = 1
        score_1 = 0
        score_2 = 0
        categorieën = ""
        db.execute("INSERT INTO spel (username, opponent, ronde, score_1, score_2, categorieën) VALUES (:username, :opponent, :ronde, :score_1, :score_2, :categorieën)", username=username, opponent=opponent, ronde=ronde,score_1=score_1 ,score_2=score_2, categorieën=categorieën)
        return redirect(url_for('fspel'))
    else:
        return render_template("gamewfriend.html")

@app.route("/spel", methods=["GET", "POST"])
@login_required
def fspel():
    if request.method == "GET":
        quest = newquestion()
        question = quest[0]
        coranswer = quest[1]
        answerlist = quest[2]
        categ = quest[3]
        session["coranswer"] = coranswer
        return render_template("friendspel.html", question=question, answerlist=answerlist, coranswer=coranswer, categ = categ)

    if request.method == "POST":
        ingevuld = str(request.form.get("answer"))
        if ingevuld == session["coranswer"]:
            session["score"] += 1
            print("goed")
        session["vraag"] += 1
        # print(vraag)
        if session["vraag"] == 10:
            session["vraag"] = 0
            return render_template("userpage.html")
        print(session["score"])
        # print(vraag)

        return redirect("/spel")

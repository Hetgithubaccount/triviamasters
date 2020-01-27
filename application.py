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

@app.route("/checkusername", methods=["GET"])
def checkusername():
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
        return redirect("/userpage")

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
@login_required
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
@login_required
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
@login_required
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
        db.execute("DELETE FROM friends WHERE username = :username and friend = :friendname", username = friendname, friendname = username)
        return redirect("/friends")
    else:
        return render_template("friends.html")

@app.route("/", methods=["GET", "POST"])
def start():
    session["score"] = 0
    session["vraag"] = 0
    session["streak"] = 0
    session["multiply"] = "X1"
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
                    db.execute("INSERT INTO spel (spelid, username, opponent, ronde, categorieën, score_1, score_2) VALUES (:spelid, :username, :opponent, :ronde, :categorieën, :score_1, :score_2)", spelid=code, username=request.form.get("username"), opponent="", ronde=1, categorieën="", score_1=0, score_2=0)
                    session["gameid"] = code
                    session["username"] = request.form.get("username")
                    return redirect("/gamewcode")

    else:
        return render_template("index.html")

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        if request.form.get("opponent") and request.form.get("number"):
            code = request.form.get("number")
            result = db.execute("SELECT * FROM spel WHERE spelid=:code", code=code)
            print(result)
            if result:
                if result[0]["opponent"] == "":
                    db.execute("UPDATE spel SET opponent=:opponent WHERE spelid=:code", opponent=request.form.get("opponent"), code=code)
                    session["gameid"] = code
                    session["username"] = request.form.get("opponent")
                    return redirect("/gamewcode")
                else:
                    return apology("already 2 players in game", 403)
            else:
                return apology("enter valid code", 403)
        else:
            return render_template("index.html")
    else:
        return render_template("index.html")

@app.route("/wacht", methods=["GET", "POST"])
def wacht():
    if request.method == "GET":
        opponent = False
        while opponent == False:
            result = db.execute("SELECT opponent FROM spel WHERE spelid=:gameid", gameid=session["gameid"])
            if result[0]["opponent"] != "":
                opponent = True

            time.sleep(.9)
        return render_template("game.html")
    else:
        return render_template("wacht.html")

@app.route("/game", methods=["GET", "POST"])
def startsinglegame():
    if request.method == "GET":
        quest = vragen()
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
            session["streak"] += 1
        else:
            session["streak"] = 0
        if session["streak"] >= 3:
            session["score"] += 1
            session["multiply"] = "X2"
        else: session["multiply"] = "X1"
        session["vraag"] += 1
        # print(vraag)
        if session["vraag"] == 10:
            session["vraag"] = 0
            return render_template("singlegameend.html")
        print(session["score"])
        # print(vraag)

        return redirect("/game")

@app.route("/singlegameend", methods=["GET", "POST"])
def singlegameend():
    if request.method == "POST":
        session.clear()
        return render_template("index.html")
    else:
        return render_template("singlegameend.html")

@app.route("/gamewcode", methods=["GET", "POST"])
def gamewcode():
    if request.method == "GET":
        quest = vragen()
        question = quest[0]
        coranswer = quest[1]
        answerlist = quest[2]
        categ = quest[3]
        username = session["username"]
        code = session["gameid"]
        session["coranswer"] = coranswer
        return render_template("gamewcode.html", question=question, answerlist=answerlist, coranswer=coranswer, categ=categ, code=code, username=username)

    if request.method == "POST":
        ingevuld = str(request.form.get("answer"))
        if ingevuld == session["coranswer"]:
            session["score"] += 1
            print("goed")
        session["vraag"] += 1
        # print(vraag)
        if session["vraag"] == 10:
            session["vraag"] = 0
            return render_template("gamewcodeend.html")
        print(session["score"])
        # print(vraag)

        return redirect("/gamewcode")

@app.route("/gamewcodeend", methods=["GET", "POST"])
def gamewcodeend():
    if request.method == "POST":
        spelid = session["gameid"]
        result1 = db.execute("SELECT score_1 FROM spel WHERE spelid=:spelid", spelid=spelid)
        result2 = db.execute("SELECT score_2 FROM spel WHERE spelid=:spelid", spelid=spelid)
        if result1 != 0 and result2 !=0:
            db.execute("DELETE * FROM spel WHERE spelid=:spelid", spelid=spelid)
            session.clear()
        return render_template("index.html")
    else:
        return render_template("gamewcodeend.html")




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
    apis = {"sport":"https://opentdb.com/api.php?amount=49&category=21&type=multiple", "geography": "https://opentdb.com/api.php?amount=49&category=22&type=multiple", "history":"https://opentdb.com/api.php?amount=49&category=23&type=multiple", "animals": "https://opentdb.com/api.php?amount=49&category=27&type=multiple"}
    api = random.choice(list(apis.keys()))
    response = requests.get(apis[api])
    sport = response.json()
    vragen = sport["results"]
    sequence = random.choice(vragen)
    category = sequence["category"]
    question = sequence["question"]
    coranswer = sequence["correct_answer"]
    answerlist = sequence["incorrect_answers"]
    answerlist.append(coranswer)
    # print(coranswer)
    return [question, coranswer, answerlist, category]

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
    if request.method == "GET":
        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        for i in username:
            for name in i:
                username = i[name]
                opponent = i[name]
        row = []
        idee = []
        spell = db.execute("SELECT * FROM spel WHERE username= :username", username=username)
        spel = db.execute("SELECT * FROM spel WHERE opponent= :opponent", opponent=opponent)
        for i in spell:
            row.append((i["opponent"],i["ronde"], i["score_1"], i["score_2"], i["spelid"]))
            idee.append((i["spelid"]))
        for i in spel:
            row.append((i["username"],i["ronde"], i["score_2"], i["score_1"], i["spelid"]))
            idee.append((i["spelid"]))
        # spelid = db.execute("SELECT spelid FROM spel WHERE username= :username AND opponent= :opponent", username=username, opponent=opponent)
        # session["gameid"] = spelid
        session["score"] = 0
        session["vraag"] = 0
        session["streak"] = 0
        ended = []
        end1 = db.execute("SELECT * FROM ended WHERE username= :username", username=username)
        end2 = db.execute("SELECT * FROM ended WHERE opponent= :opponent", opponent=opponent)
        for i in end1:
            ended.append(i["opponent"], i["score_1"], i["score_2"])
        for i in end2:
            ended.append(i["username"], i["score_2"], i["score_1"])


        return render_template("userpage.html", spell=spell, idee=idee, spel=spel, row=row, ended=ended)
    else:
        return render_template("userpage.html")

@app.route("/play", methods=["GET", "POST"])
@login_required
def gamewfriend():
    session["score"] = 0
    session["vraag"] = 0
    if request.method == "POST":
        opponent = request.form.get("f-opponent")
        if not opponent:
             return apology("must insert friends username", 403)
        id = session["user_id"]
        username = db.execute("SELECT username FROM users WHERE id = :id", id=id)
        for i in username:
            for name in i:
                username = i[name]
        friend = db.execute("SELECT friend FROM friends WHERE username = :username",
                          username=username)
        if not friend:
             return apology("must add opponent as friend", 403)
        gespeeld = db.execute("SELECT spelid FROM spel WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
        if gespeeld:
            return apology("you can only play 1 game per friend at the moment", 403)
        ronde_1 = 1
        ronde_2 = 1
        score_1 = 0
        score_2 = 0
        ronde = 1
        categorieën = ""
        db.execute("INSERT INTO spel (username, opponent, ronde_1, ronde_2, ronde, score_1, score_2, categorieën) VALUES (:username, :opponent, :ronde_1, :ronde_2, :ronde, :score_1, :score_2, :categorieën)", username=username, opponent=opponent, ronde_1=ronde_1, ronde_2=ronde_2, ronde=ronde,score_1=score_1 ,score_2=score_2, categorieën=categorieën)
        spelid = db.execute("SELECT spelid FROM spel WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
        session["spelid"] = spelid[0]["spelid"]
        return redirect(url_for('fspel'))
    else:
        return render_template("gamewfriend.html")

@app.route("/spel", methods=["GET", "POST"])
@login_required
def fspel():
    if request.method == "GET":
        id = session["user_id"]
        username = db.execute("SELECT username FROM users WHERE id = :id", id=id)
        for i in username:
            for name in i:
                username = i[name]
        spelid= session["spelid"]
        naam = db.execute("SELECT username FROM spel WHERE spelid=:spelid", spelid=spelid)
        ronde_1 = db.execute("SELECT ronde_1 FROM spel WHERE spelid=:spelid", spelid=spelid)
        print(ronde_1)
        ronde_2 = db.execute("SELECT ronde_2 FROM spel WHERE spelid=:spelid", spelid=spelid)
        ronde_1 = ronde_1[0]["ronde_1"]
        ronde_2 = ronde_2[0]["ronde_2"]
        naam = naam[0]["username"]
        if naam == username:
            if ronde_1 > ronde_2:
                return apology("wait till opponent has played the previous round", 403)
        else:
            if ronde_2 > ronde_1:
                return apology("wait till opponent has played the previous round", 403)


        # session["spelid"] = request.args.get("id")
        quest = vragen()
        question = quest[0]
        coranswer = quest[1]
        answerlist = set(quest[2])
        print(answerlist)
        categ = quest[3]
        session["coranswer"] = coranswer
        return render_template("friendspel.html", question=question, answerlist=answerlist, coranswer=coranswer, categ = categ)

    if request.method == "POST":
        spelid= session["spelid"]
        ingevuld = str(request.form.get("answer"))
        if ingevuld == session["coranswer"]:
            session["score"] += 1
            session["streak"] += 1
        else:
            session["streak"] = 0
        session["vraag"] += 1
        # print(vraag)
        if session["streak"] >= 3:
            session["score"] += 1
            session["multiply"] = "X2"
        else:
            session["multiply"] = "X1"
        if session["vraag"] == 10:
            session["vraag"] = 0
            id = session["user_id"]
            username = db.execute("SELECT username FROM users WHERE id = :id", id=id)
            for i in username:
                for name in i:
                    username = i[name]
            score = session["score"]
            naam = db.execute("SELECT username FROM spel WHERE spelid=:spelid", spelid=spelid)
            naam = naam[0]["username"]
            if naam == username:
                score_oud = (db.execute("SELECT score_1 FROM spel WHERE spelid=:spelid", spelid=spelid))
                score = score + score_oud[0]['score_1']
                session["score_1"] = score
                ronde_oud = db.execute("SELECT ronde_1 FROM spel WHERE spelid=:spelid", spelid=spelid)
                ronde = ronde_oud[0]['ronde_1'] + 1
                db.execute("UPDATE spel SET ronde_1 = :ronde, score_1 = :score WHERE spelid = :spelid", ronde=ronde, score=score, spelid=spelid)
            else:
                 score_oud= (db.execute("SELECT score_2 FROM spel WHERE spelid=:spelid", spelid=spelid))
                 score = score + score_oud[0]['score_2']
                 session["score_2"] = score
                 ronde_oud = db.execute("SELECT ronde_2 FROM spel WHERE spelid=:spelid", spelid=spelid)
                 ronde = ronde_oud[0]['ronde_2'] + 1
                 db.execute("UPDATE spel SET ronde_2 = :ronde, score_2 = :score WHERE spelid = :spelid", ronde=ronde, score=score, spelid=spelid)
            ronde_2= (db.execute("SELECT ronde_2 FROM spel WHERE spelid=:spelid", spelid=spelid))
            ronde_1= (db.execute("SELECT ronde_1 FROM spel WHERE spelid=:spelid", spelid=spelid))
            print(ronde_2, ronde_1, "test")
            ronde_1 = ronde_1[0]["ronde_1"]
            ronde_2 = ronde_2[0]["ronde_2"]
            if ronde_2 == ronde_1:
                 ronde = ronde_1
                 print(ronde, "test")
                 db.execute("UPDATE spel SET ronde = :ronde WHERE spelid = :spelid", ronde=ronde, spelid=spelid)
                 if ronde == 5:
                     score_1 = session["score_1"]
                     score_2 = db.execute("SELECT score_2 FROM spel WHERE spelid = :spelid", spelid=spelid)
                     opponent = (db.execute("SELECT opponent FROM spel WHERE spelid=:spelid", spelid=spelid))
                     db.execute("INSERT INTO ended (username, opponent, score_1, score_2, spelid) VALUES (:username, :opponent, :score_1, :score_2, :spelid)" ,username=username, opponent=opponent, score_1=score_1, score_2=score_2, spelid=spelid)
                     hscore_1 = db.execute("SELECT highscore FROM users WHERE username= :username", username=username)
                     hscore_2 = db.execute("SELECT highscore FROM users WHERE username= :opponent", opponent=opponent)
                     if score_1 > hscore_1:
                         db.execute("UPDATE users SET highscore = :hscore_1 WHERE username = :username", hscore_1= hscore_1, username=username)
                     if score_2 > hscore_2:
                          db.execute("UPDATE users SET highscore = :hscore_2 WHERE username = :opponent", hscore_2=hscore_2, opponent=opponent)
            return redirect("/userpage")
        return redirect("/spel")

@app.route("/leaderboards", methods=["GET", "POST"])
@login_required
def leaderbords():
    if request.method == "POST":
        hscores= db.execute ("select * FROM users")
        print(hscores)
        return render_template("leaderboards.html", hscores=hscores)
    else:
        hscores= db.execute("select * FROM users")
        print(hscores)
        return render_template("leaderboards.html", hscores=hscores)

@app.route("/about", methods=["GET", "POST"])
def about():
    if request.method == "POST":
        return render_template("about.html")
    else:
        return render_template("about.html")

@app.route("/rspel", methods=["GET", "POST"])
@login_required
def rspel():
    if request.method == "post":
        spelid = request.form.get("delete")
        print(spelid)
        db.execute("DELETE FROM spel WHERE spelid = :spelid", spelid = spelid)
        return render_template("userpage.html")
    else:
        spelid = request.form.get("delete")
        print(spelid)
        db.execute("DELETE FROM spel WHERE spelid = :spelid", spelid = spelid)
        return redirect("/userpage")

@app.route("/doorverwijs", methods=["GET", "POST"])
@login_required
def doorverwijs():
    if request.method == "post":
        session["spelid"] = request.form.get("id")
        print(session["spelid"], "test")
        return render_template("spel.html")
    else:
        session["spelid"] = request.form.get("id")
        print(session["spelid"], "test")
        return render_template("doorverwijs.html")
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

from helpers import apology, login_required, vragen, user, row_users
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
        result = row_users(request.form.get("username"))
        # checks if username is in use
        if result:
            return apology("Username already exist", 400)

        # creates user
        highscore = 0
        session["user_id"] = db.execute("INSERT INTO users (username, hash, highscore) \
                             VALUES(:username, :hash, :highscore)", \
                             username=request.form.get("username"), \
                             hash=generate_password_hash(request.form.get("password")), highscore=highscore)

        return render_template("userpage.html")

    else:
        return render_template("register.html")

@app.route("/checkusername", methods=["GET"])
def checkusername():
    """Return true if username available/registered, else false, in JSON format"""
    result = row_users( username=request.args.get("username"))
    if len(result) > 0:
        return jsonify(False)
    else:
        return jsonify(True)

@app.route("/checkpassword", methods=["GET"])
def checkpassword():
    """Return true if password is correct, else false, in JSON format"""
    username = request.args.get("username")
    password = request.args.get("password")
    result = row_users(username)

    if check_password_hash(result[0]["hash"], password):
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

# Checked for code quality 28/01/2019 by Nathan
@app.route("/friends", methods=["GET", "POST"])
@login_required
def findfriends():
    if request.method == "GET":

        # Collects username
        username = user()
        # Collects friends that user invited
        ownfriends = db.execute("SELECT * FROM friends WHERE username = :username", username = username)
        # Collects others that invited user to be friend (necessary because of database columns)
        reversefriends = db.execute("SELECT * FROM friends WHERE friend = :friend", friend = username)
        # Swaps variables when user is "friend" in db to make sure information is displayed correctly,
        # e.g. swaps names and amount of wins/losses
        for i in reversefriends:
            dude = i["username"]
            i["username"] = i["friend"]
            i["friend"] = dude
            games_won = i["won"]
            i["won"] = i["lose"]
            i["lose"] = games_won
        # Compiles info, everything is now in the same order
        portfolio_contents = ownfriends + reversefriends

        return render_template("friends.html", portfolio_contents = portfolio_contents)
    else:
        return render_template("friends.html")

# Checked for code quality 28/01/2019 by Nathan
@app.route("/addfriend", methods=["GET", "POST"])
@login_required
def addfriend():
    if request.method == "POST":

        # Collects name of friend
        friendname = request.form.get("addusername")
        # Checks if username is legit
        result = row_users( request.form.get("addusername"))
        if not result:
            return apology("user does not exist", 403)
        # Collects username
        username = user()
        # Database insert and reset of games/wins/losses
        db.execute("INSERT INTO friends (username, friend, games, won, lose)  \
                    VALUES (:username, :friend, :games, :won, :lose)", username = username, friend = friendname, games = 0, won = 0, lose = 0)
        return redirect("/friends")
    else:
        return render_template("friends.html")

# Checked for code quality 28/01/2019 by Nathan
@app.route("/delfriend", methods=["GET", "POST"])
@login_required
def delfriend():
    if request.method == "POST":

        # Collects name of friend
        friendname = request.form.get("delusername")
        # Checks if username is legit
        result= row_users(request.form.get("delusername"))
        if not result:
            return apology("user does not exist", 403)
        # Collects username
        username = user()
        # Deletes friend (both cases are covered, so both users can delete the friendship)
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
        # Starts a singleplayer game
        if request.form.get("singleplayer"):
            return render_template("game.html")

        # Checks for correct input
        elif not request.form.get("username") and not request.form.get("opponent"):
            return apology("must provide username", 403)
        elif request.form.get("opponent") and not request.form.get("number"):
            return apology("must provide code", 403)

        # Starts a game with code
        elif request.form.get("username"):
            # Determines amount of questions
            if request.form.get("q_amount"):
                q_amount = int(request.form.get("q_amount"))
            else:
                q_amount = 10

            # Database entry for gamewcode
            newgame = True
            while newgame:
                code = random.randrange(100000, 999999)
                result = db.execute("SELECT * FROM codegames WHERE gameid=:code", code=code)
                if not result:
                    db.execute("INSERT INTO codegames (gameid, username, opponent, score_1, score_2, q_amount, finished)  \
                                VALUES (:gameid, :username, :opponent, :score_1, :score_2, :q_amount, :finished)",   \
                                gameid=code, username=request.form.get("username"), opponent="", score_1=0, score_2=0,   \
                                q_amount=q_amount, finished=0)
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
            result = db.execute("SELECT * FROM codegames WHERE gameid=:code", code=code)
            if result:
                if result[0]["opponent"] == "":
                    db.execute("UPDATE codegames SET opponent=:opponent WHERE gameid=:code",  \
                                opponent=request.form.get("opponent"), code=code)
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

# Checked for code quality 28/01/2019 by Nathan
@app.route("/game", methods=["GET", "POST"])
def startsinglegame():
    if request.method == "GET":

        # Collects question and uses indexation to grab each individual part of the database output
        quest = vragen()
        question = quest[0]
        coranswer = quest[1]
        answerlist = set(quest[2])
        categ = quest[3]
        # Saves correct answer to be used later
        session["coranswer"] = coranswer

        # Question is rendered on screen
        return render_template("game.html", question=question, answerlist=answerlist, coranswer=coranswer, categ = categ)

    # After question is answered
    if request.method == "POST":

        # Collects user answer
        answer = str(request.form.get("answer"))
        # Answer is correct, score and streak are updated
        if answer == session["coranswer"]:
            session["score"] += 1
            session["streak"] += 1
        # Answer is incorrect, streak back to zero
        else:
            session["streak"] = 0
        # If user has answer streak, extra point is given and graphic is updated
        if session["streak"] >= 3:
            session["score"] += 1
            session["multiply"] = "X2"
        # Graphic when user has no answer streak
        else: session["multiply"] = "X1"
        # Question amount is updated
        session["vraag"] += 1
        # Ends game if 10 questions have been answered
        if session["vraag"] == 10:
            session["vraag"] = 0
            return render_template("singlegameend.html")
        # Restarts and generates new question
        return redirect("/game")

# Checked for code quality 28/01/2019 by Nathan
@app.route("/singlegameend", methods=["GET", "POST"])
def singlegameend():
    if request.method == "POST":
        # Clears question information
        session.clear()
        # Returns to start page
        return render_template("index.html")
    else:
        return render_template("singlegameend.html")

@app.route("/gamewcode", methods=["GET", "POST"])
def gamewcode():
    if request.method == "GET":
        # Sets up the gamepage
        quest = vragen()
        question = quest[0]
        coranswer = quest[1]
        answerlist = set(quest[2])
        categ = quest[3]
        username = session["username"]
        code = session["gameid"]
        session["coranswer"] = coranswer
        return render_template("gamewcode.html", question=question, answerlist=answerlist,  \
                                coranswer=coranswer, categ=categ, code=code, username=username)

    if request.method == "POST":
        # Checks answer and handles accordingly
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

        # Checks if game is completed
        q_amount = db.execute("SELECT q_amount FROM codegames WHERE gameid=:gameid", gameid=session["gameid"])[0]["q_amount"]
        if session["vraag"] == q_amount:
            session["vraag"] = 0
            return render_template("gamewcodeend.html")

        return redirect("/gamewcode")

@app.route("/gamewcodeend", methods=["GET", "POST"])
def gamewcodeend():
    if request.method == "POST":
        return render_template("gamewcodeend.html")
    else:
        return render_template("gamewcodeend.html")

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
        username = user()
        opponent = username
        row = []
        idee = []
        spell = db.execute("SELECT * FROM spel WHERE username= :username", username=username)
        spel = db.execute("SELECT * FROM spel WHERE opponent= :opponent", opponent=opponent)
        for i in spell:
            row.append((i["opponent"],i["ronde"], i["score_1"], i["score_2"], i["gameid"]))
            idee.append((i["gameid"]))
        for i in spel:
            row.append((i["username"],i["ronde"], i["score_2"], i["score_1"], i["gameid"]))
            idee.append((i["gameid"]))
        session["score"] = 0
        session["vraag"] = 0
        session["streak"] = 0
        ended = []
        end1 = db.execute("SELECT * FROM ended WHERE username= :username", username=username)
        end2 = db.execute("SELECT * FROM ended WHERE opponent= :opponent", opponent=opponent)
        for i in end1:
            a = [i["opponent"], i["score_1"], i["score_2"]]
            ended.append(a)
        for i in end2:
            a= [i["username"], i["score_2"], i["score_1"]]
            ended.append(a)
        return render_template("userpage.html", spell=spell, idee=idee, spel=spel, row=row, ended=ended)
    else:
        return render_template("userpage.html")

@app.route("/play", methods=["GET", "POST"])
@login_required
def gamewfriend():
    #get session values for score amount of questions and the current ronde
    session["score"] = 0
    session["vraag"] = 0
    session["ronde"] = 1
    if request.method == "POST":
        # Get opponent name from form
        opponent = request.form.get("f-opponent")
        # Check if the form is not empty
        if not opponent:
             return apology("must insert friends username", 403)
        # Get username
        username = user()
        # Check in friends database if user has added opponent as friend
        friend = db.execute("SELECT friend FROM friends WHERE username = :username",
                          username=username)
        friend2 = db.execute("SELECT username FROM friends WHERE friend = :username",
                          username=username)
        # Check if players are friends
        if not friend and not friend2:
             return apology("must add opponent as friend", 403)
        # Query in spel if players already playing a game against each other at the moment
        current_game = db.execute("SELECT gameid FROM spel WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
        if current_game:
            return apology("you can only play 1 game per friend at the moment", 403)
        # Make a new game in the database
        ronde_1 = 1
        ronde_2 = 1
        score_1 = 0
        score_2 = 0
        ronde = 1
        categorieën = ""
        db.execute("INSERT INTO spel (username, opponent, ronde_1, ronde_2, ronde, score_1, score_2, categorieën) VALUES (:username, :opponent, :ronde_1, :ronde_2, :ronde, :score_1, :score_2, :categorieën)", username=username, opponent=opponent, ronde_1=ronde_1, ronde_2=ronde_2, ronde=ronde,score_1=score_1 ,score_2=score_2, categorieën=categorieën)
        gameid = db.execute("SELECT gameid FROM spel WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
        session["gameid"] = gameid[0]["gameid"]
        return redirect(url_for('fspel'))
    else:
        return render_template("gamewfriend.html")

@app.route("/spel", methods=["GET", "POST"])
@login_required
def fspel():
    if request.method == "GET":
        # Get username of user
        username = user()
        # Get gameid
        gameid= session["gameid"]
        session["ronde"] = db.execute("SELECT ronde FROM spel WHERE gameid= :gameid", gameid=gameid)[0]["ronde"]
        naam = db.execute("SELECT username FROM spel WHERE gameid=:gameid", gameid=gameid)
        ronde_1 = db.execute("SELECT ronde_1 FROM spel WHERE gameid=:gameid", gameid=gameid)
        ronde_2 = db.execute("SELECT ronde_2 FROM spel WHERE gameid=:gameid", gameid=gameid)
        ronde_1 = ronde_1[0]["ronde_1"]
        ronde_2 = ronde_2[0]["ronde_2"]
        naam = naam[0]["username"]
        if naam == username:
            # Checks if player one is in the same ronde as player 2
            if ronde_1 > ronde_2:
                return apology("wait till opponent has played the previous ronde", 403)
        else:
            if ronde_2 > ronde_1:
                return apology("wait till opponent has played the previous ronde", 403)


        # Collects question and uses indexation to grab each individual part of the database output
        quest = vragen()
        question = quest[0]
        coranswer = quest[1]
        answerlist = set(quest[2])
        categ = quest[3]
        session["coranswer"] = coranswer
        # Return the data of the question to friendspel.html
        return render_template("friendspel.html", question=question, answerlist=answerlist, coranswer=coranswer, categ = categ)
    # If the player clicks on an answer
    if request.method == "POST":
        # Get gameid
        gameid= session["gameid"]
        # Get the answer the user has chosen
        ingevuld = str(request.form.get("answer"))
        # Check if the answer is the right one, if yes score +1 and streak + 1, if not reset streak
        if ingevuld == session["coranswer"]:
            session["score"] += 1
            session["streak"] += 1
        else:
            session["streak"] = 0
        # The answered question count + 1
        session["vraag"] += 1
        # Check if streak is more than 3 to activate multiplier (correct answer is 2 points)
        if session["streak"] >= 3:
            session["score"] += 1
            session["multiply"] = "X2"
        else:
            session["multiply"] = "X1"
        # After 10 questions the ronde is finished
        if session["vraag"] == 10:
            session["vraag"] = 0
            # Get username of user
            username = user()
            # Get the endscore and the name of the person who started the game
            score = session["score"]
            naam = db.execute("SELECT username FROM spel WHERE gameid=:gameid", gameid=gameid)
            naam = naam[0]["username"]
            # If the current user is the same as the player who started the game, get score_1 from spel and add the reached score. Also update ronde
            if naam == username:
                score_oud = (db.execute("SELECT score_1 FROM spel WHERE gameid=:gameid", gameid=gameid))
                score = score + score_oud[0]['score_1']
                session["score_1"] = score
                ronde_oud = db.execute("SELECT ronde_1 FROM spel WHERE gameid=:gameid", gameid=gameid)
                ronde = ronde_oud[0]['ronde_1'] + 1
                db.execute("UPDATE spel SET ronde_1 = :ronde, score_1 = :score WHERE gameid = :gameid", ronde=ronde, score=score, gameid=gameid)
            # If the current user is not the game starter get score_2 from spel and update it with the reached score
            else:
                 score_oud= (db.execute("SELECT score_2 FROM spel WHERE gameid=:gameid", gameid=gameid))
                 score = score + score_oud[0]['score_2']
                 session["score_2"] = score
                 ronde_oud = db.execute("SELECT ronde_2 FROM spel WHERE gameid=:gameid", gameid=gameid)
                 ronde = ronde_oud[0]['ronde_2'] + 1
                 db.execute("UPDATE spel SET ronde_2 = :ronde, score_2 = :score WHERE gameid = :gameid", ronde=ronde, score=score, gameid=gameid)
            # Get the amount of rondes the users has played. if the ronde is the same, the ronde index for userpage can be updated
            ronde_2= (db.execute("SELECT ronde_2 FROM spel WHERE gameid=:gameid", gameid=gameid))[0]["ronde_2"]
            ronde_1= (db.execute("SELECT ronde_1 FROM spel WHERE gameid=:gameid", gameid=gameid))[0]["ronde_1"]
            if ronde_2 == ronde_1:
                 ronde = ronde_1
                 db.execute("UPDATE spel SET ronde = :ronde WHERE gameid = :gameid", ronde=ronde, gameid=gameid)
                 # If the players played 4 rondes get the endscores and the names of the players and insert the data in the table ended
                 if ronde == 5:
                     score_1 = db.execute("SELECT score_1 FROM spel WHERE gameid = :gameid", gameid=gameid)[0]["score_1"]
                     score_2 = db.execute("SELECT score_2 FROM spel WHERE gameid = :gameid", gameid=gameid)[0]["score_2"]
                     opponent = db.execute("SELECT opponent FROM spel WHERE gameid=:gameid", gameid=gameid)[0]["opponent"]
                     username = db.execute("SELECT username FROM spel WHERE gameid=:gameid", gameid=gameid)[0]["username"]
                     db.execute("INSERT INTO ended (username, opponent, score_1, score_2, gameid) VALUES (:username, :opponent, :score_1, :score_2, :gameid)" ,username=username, opponent=opponent, score_1=score_1, score_2=score_2, gameid=gameid)

                     # Determines who is "username" and who is "friend" in database
                     friends_username = db.execute("SELECT friend FROM friends WHERE username = :username", username = username)
                     friends_opponent = db.execute("SELECT friend FROM friends WHERE username = :username", username = opponent)
                     # If username = username and friend = opponent
                     for dic in friends_username:
                         if dic["friend"] == opponent:
                            db.execute("UPDATE friends SET games = games + 1 WHERE username = :username and friend = :friend", username = username, friend = opponent)
                            # If username won the game
                            if score_1 > score_2:
                                db.execute("UPDATE friends SET won = won + 1 WHERE username = :username and friend = :friend", username = username, friend = opponent)
                            # If opponent won the game
                            if score_2 > score_1:
                                db.execute("UPDATE friends SET lose = lose + 1 WHERE username = :username and friend = :friend", username = username, friend = opponent)
                     # If username = opponent and friend = username
                     for dic in friends_opponent:
                         if dic["friend"] == username:
                            db.execute("UPDATE friends SET games = games + 1 WHERE username = :username and friend = :friend", username = opponent, friend = username)
                            # If username won the game
                            if score_1 < score_2:
                                db.execute("UPDATE friends SET won = won + 1 WHERE username = :username and friend = :friend", username = opponent, friend = username)
                            # If opponent won the game
                            if score_2 < score_1:
                                db.execute("UPDATE friends SET lose = lose + 1 WHERE username = :username and friend = :friend", username = opponent, friend = username)
                     # Get the current highscores of the players
                     hscore_1 = db.execute("SELECT highscore FROM users WHERE username= :username", username=username)[0]["highscore"]
                     hscore_2 = db.execute("SELECT highscore FROM users WHERE username= :opponent", opponent=opponent)[0]["highscore"]
                     # IF the score of the game maker is higher than his/her highscore, update
                     if score_1 > int(hscore_1):
                         db.execute("UPDATE users SET highscore = :score_1 WHERE username = :username", score_1= score_1, username=username)
                     # If the score of the game joiner is higher than his/her highscore, update
                     if score_2 > int(hscore_2):
                         db.execute("UPDATE users SET highscore = :score_2 WHERE username = :opponent", score_2=score_2, opponent=opponent)
                     # Delete the game
                     db.execute("DELETE FROM spel WHERE gameid = :gameid", gameid=gameid)
                     return redirect("/userpage")
            return redirect("/userpage")
        return redirect("/spel")

@app.route("/leaderboards", methods=["GET", "POST"])
@login_required
def leaderbords():
    if request.method == "POST":
        return render_template("leaderboards.html")
    else:
        # Get all highscores from the database users
        hscores= db.execute("SELECT highscore, username FROM users")
        # Make a list with the numbers 1 till 10
        user_count = []
        for i in range(11):
            if i > 0:
                user_count.append(i)

        # Sort the highscores from highest to lowest and select the best 10
        hscores = (sorted(hscores, key = lambda i: int(i['highscore']), reverse=True))[:10]
        # Zip the lists together to make a the jinja forloop possible
        rangschikking = zip(hscores,user_count)
        # Send the lists to leaderboards.html
        return render_template("leaderboards.html", rangschikking=rangschikking)

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
        return render_template("userpage.html")
    else:
        # Get value(gameid) from the clicked button
        gameid = request.form.get("delete")
        # Delete game from database
        db.execute("DELETE FROM spel WHERE gameid = :gameid", gameid = gameid)
        return redirect("/userpage")

@app.route("/doorverwijs", methods=["GET", "POST"])
@login_required
def doorverwijs():
    if request.method == "post":
        return render_template("spel.html")
    else:
        # Get value(gameid) from the clicked button, and save the gameid in session
        session["gameid"] = request.form.get("id")
        return render_template("doorverwijs.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "post":
        code = session["gameid"]

        result1 = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["score_1"]
        result2 = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["score_2"]
        if session["username"] == db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["username"]:
            session["score_2"] = result2
            if result2 > result1:
                session["winner"] = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["opponent"]
            elif result1 > result2:
                session["winner"] = session["username"]
            else:
                session["winner"] = "Draw"
        else:
            session["score_2"] = result1
            if result1 > result2:
                session["winner"] = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["opponent"]
            elif result2 > result1:
                session["winner"] = session["username"]
            else:
                session["winner"] = "Draw"

        if result1 != 0 and result2 !=0:
            db.execute("DELETE * FROM gamecodes WHERE gameid=:gameid", gameid=code)
            session.clear()
        return render_template("result.html")
    else:
        return render_template("result.html")

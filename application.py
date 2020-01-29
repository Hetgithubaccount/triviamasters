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

from helpers import apology, login_required, questions, user, row_users
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
    """ Enables user to create account """
    if request.method == "POST":

        # Checks if username is filled in
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Checks if password was filled in
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Checks if passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password doesn't match", 400)
        result = row_users(request.form.get("username"))
        # Checks if username is in use
        if result:
            return apology("Username already exist", 400)

        # Creates user
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
            return render_template("login.html")

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
    """ Collects user's friends from database """
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


@app.route("/addfriend", methods=["GET", "POST"])
@login_required
def addfriend():
    """ Enables user to add friend """
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

@app.route("/delfriend", methods=["GET", "POST"])
@login_required
def delfriend():
    """ Enables user to delete friend """
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
    """ Displays homepage and sets values for later use in games """
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
                # Makes a new game in database
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
    """ Enables user to join a game through a code """
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
        quest = questions()
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
        quest = questions()
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
        else:
            session["multiply"] = "X1"
        session["vraag"] += 1

        # Checks if game is completed
        q_amount = db.execute("SELECT q_amount FROM codegames WHERE gameid=:gameid", gameid=session["gameid"])[0]["q_amount"]
        if session["vraag"] == q_amount:
            session["vraag"] = 0
            if session["username"] == db.execute("SELECT username FROM codegames WHERE gameid=:gameid", gameid=session["gameid"])[0]["username"]:
                db.execute("UPDATE codegames SET score_1=:score WHERE gameid=:code",  \
                                score=session["score"], code=session["gameid"])
            else:
                db.execute("UPDATE codegames SET score_2=:score WHERE gameid=:code",  \
                                score=session["score"], code=session["gameid"])
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
        game1 = db.execute("SELECT * FROM game WHERE username= :username", username=username)
        game = db.execute("SELECT * FROM game WHERE opponent= :opponent", opponent=opponent)
        for i in game1:
            row.append((i["opponent"],i["round"], i["score_1"], i["score_2"], i["gameid"]))
        for i in game:
            row.append((i["username"],i["round"], i["score_2"], i["score_1"], i["gameid"]))
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
        return render_template("userpage.html", row=row, ended=ended)
    else:
        return render_template("userpage.html")

@app.route("/play", methods=["GET", "POST"])
@login_required
def gamewfriend():
    #get session values for score amount of questions and the current round
    session["score"] = 0
    session["vraag"] = 0
    session["round"] = 1
    session["multiply"] = "X1"
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
        # Query in game if players already playing a game against each other at the moment
        current_game = db.execute("SELECT gameid FROM game WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
        if current_game:
            return apology("you can only play 1 game per friend at the moment", 403)
        # Make a new game in the database
        round_1 = 1
        round_2 = 1
        score_1 = 0
        score_2 = 0
        round = 1
        categorieën = ""
        db.execute("INSERT INTO game (username, opponent, round_1, round_2, round, score_1, score_2, categorieën) VALUES (:username, :opponent, :round_1, :round_2, :round, :score_1, :score_2, :categorieën)", username=username, opponent=opponent, round_1=round_1, round_2=round_2, round=round,score_1=score_1 ,score_2=score_2, categorieën=categorieën)
        gameid = db.execute("SELECT gameid FROM game WHERE username= :username AND opponent = :opponent", username=username, opponent=opponent )
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
        session["round"] = db.execute("SELECT round FROM game WHERE gameid= :gameid", gameid=gameid)[0]["round"]
        name = db.execute("SELECT username FROM game WHERE gameid=:gameid", gameid=gameid)
        round_1 = db.execute("SELECT round_1 FROM game WHERE gameid=:gameid", gameid=gameid)
        round_2 = db.execute("SELECT round_2 FROM game WHERE gameid=:gameid", gameid=gameid)
        round_1 = round_1[0]["round_1"]
        round_2 = round_2[0]["round_2"]
        name = name[0]["username"]
        if name == username:
            # Checks if player one is in the same round as player 2
            if round_1 > round_2:
                return apology("wait till opponent has played the previous round", 403)
        else:
            if round_2 > round_1:
                return apology("wait till opponent has played the previous round", 403)


        # Collects question and uses indexation to grab each individual part of the database output
        quest = questions()
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
        # After 10 questions the round is finished
        if session["vraag"] == 10:
            session["vraag"] = 0
            # Get username of user
            username = user()
            # Get the endscore and the name of the person who started the game
            score = session["score"]
            name = db.execute("SELECT username FROM game WHERE gameid=:gameid", gameid=gameid)
            name = name[0]["username"]
            # If the current user is the same as the player who started the game, get score_1 from game and add the reached score. Also update round
            if name == username:
                score_old = (db.execute("SELECT score_1 FROM game WHERE gameid=:gameid", gameid=gameid))
                score = score + score_old[0]['score_1']
                session["score_1"] = score
                round_old = db.execute("SELECT round_1 FROM game WHERE gameid=:gameid", gameid=gameid)
                round = round_old[0]['round_1'] + 1
                db.execute("UPDATE game SET round_1 = :round, score_1 = :score WHERE gameid = :gameid", round=round, score=score, gameid=gameid)
            # If the current user is not the game starter get score_2 from game and update it with the reached score
            else:
                score_old= (db.execute("SELECT score_2 FROM game WHERE gameid=:gameid", gameid=gameid))
                score = score + score_old[0]['score_2']
                session["score_2"] = score
                round_old = db.execute("SELECT round_2 FROM game WHERE gameid=:gameid", gameid=gameid)
                round = round_old[0]['round_2'] + 1
                db.execute("UPDATE game SET round_2 = :round, score_2 = :score WHERE gameid = :gameid", round=round, score=score, gameid=gameid)
            # Get the amount of rounds the users has played. if the round is the same, the round index for userpage can be updated
            round_2= (db.execute("SELECT round_2 FROM game WHERE gameid=:gameid", gameid=gameid))[0]["round_2"]
            round_1= (db.execute("SELECT round_1 FROM game WHERE gameid=:gameid", gameid=gameid))[0]["round_1"]
            if round_2 == round_1:
                round = round_1
                db.execute("UPDATE game SET round = :round WHERE gameid = :gameid", round=round, gameid=gameid)
                # If the players played 4 rounds get the endscores and the names of the players and insert the data in the table ended
                if round == 5:
                    score_1 = db.execute("SELECT score_1 FROM game WHERE gameid = :gameid", gameid=gameid)[0]["score_1"]
                    score_2 = db.execute("SELECT score_2 FROM game WHERE gameid = :gameid", gameid=gameid)[0]["score_2"]
                    opponent = db.execute("SELECT opponent FROM game WHERE gameid=:gameid", gameid=gameid)[0]["opponent"]
                    username = db.execute("SELECT username FROM game WHERE gameid=:gameid", gameid=gameid)[0]["username"]
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
                    db.execute("DELETE FROM game WHERE gameid = :gameid", gameid=gameid)
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
        ranking = zip(hscores,user_count)
        # Send the lists to leaderboards.html
        return render_template("leaderboards.html", ranking=ranking)

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
        db.execute("DELETE FROM game WHERE gameid = :gameid", gameid = gameid)
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
        return render_template("result.html")
    else:
        code = session["gameid"]

        result1 = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["score_1"]
        result2 = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["score_2"]
        if session["username"] == db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["username"]:
            session["score_2"] = result2
            print(session["score_2"])
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
                session["winner"] = "It's a draw"
        finished = db.execute("SELECT * FROM codegames WHERE gameid=:gameid", gameid=code)[0]["finished"]

        if finished == 2:
            db.execute("DELETE * FROM codegames WHERE gameid=:gameid", gameid=code)
            session.clear()
        return render_template("result.html")

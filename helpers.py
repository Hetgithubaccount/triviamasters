import requests
import urllib.parse
import os
import random
import sqlite3
from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

db = SQL("sqlite:///trivia.db")
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def questions():
    response = requests.get("https://opentdb.com/api.php?amount=49&category=21&type=multiple")
    apis = {"sport":"https://opentdb.com/api.php?amount=49&category=21&type=multiple",  \
            "geography": "https://opentdb.com/api.php?amount=49&category=22&type=multiple",  \
            "history":"https://opentdb.com/api.php?amount=49&category=23&type=multiple",  \
            "animals": "https://opentdb.com/api.php?amount=49&category=27&type=multiple"}
    api = random.choice(list(apis.keys()))
    response = requests.get(apis[api])
    sport = response.json()
    all_questions = sport["results"]
    sequence = random.choice(all_questions)
    category = sequence["category"]
    question = sequence["question"]
    coranswer = sequence["correct_answer"]
    answerlist = sequence["incorrect_answers"]
    answerlist.append(coranswer)
    # print(coranswer)
    return [question, coranswer, answerlist, category]

def user():
    id = session["user_id"]
    username = db.execute("SELECT username FROM users WHERE id = :id", id=id)[0]["username"]
    return username

def row_users(username):
    result = db.execute("SELECT * FROM users \
                            WHERE username=:username", username=username)
    return result
@app.route("/play", methods=["GET", "POST"])
@login_required
def gamewfriend():
    if request.method == "POST":
        opponent = request.form.get("f-opponent")
        if not opponent:
             return apology("must insert friends username", 403)
             id = session["user_id"]
             username = db.execute("SELECT username FROM users WHERE id = : id", id=id)
        friend = db.execute("SELECT friend FROM friends WHERE username = :username",
                          username=username)
        if not friend:
             return apology("must add opponent as friend", 403)
        return render_template("userpage.html")
    else:
        return render_template("gamewfriend.html")
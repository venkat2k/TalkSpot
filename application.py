from flask import *
import requests
from flask import *
import pymysql
import datetime

app = Flask(__name__)
app.secret_key = "secret key"

connection = pymysql.connect(host="localhost", user="root", passwd="", database="talkspot")
cursor = connection.cursor()


f = open("words.txt", "r")
filecontent = f.read()
words = filecontent.split("\n")
f.close()

def analyze(text):
    text = text.split()
    for word in words:
        for x in text:
            if x == word:
                return 0
    return 1

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    sql = "SELECT * FROM talks ORDER BY talkid desc LIMIT 10;"
    cursor.execute(sql)
    recents = cursor.fetchall()
    username = session['username']
    if 'data' in session:
        data = session['data']
        session.pop('data', None)
        return render_template("homepage.html", data = data, recents = recents, username = username)
    return render_template("homepage.html", data = None, recents = recents, username = username)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for('index'))
    if request.method == "POST":
        username = request.form.get("username")
        pwd = request.form.get("pwd")
        sql = "SELECT * FROM users WHERE username = '{0}' AND password = '{1}';".format(username, pwd)
        cursor.execute(sql)
        rows = cursor.fetchall()
        if len(rows) == 1:
            session['username'] = username
            return redirect(url_for("index"))
        else:
            flash("Username or password is incorrect.")
    return render_template("login.html")

@app.route("/logout", methods = ["GET"])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/signup", methods = ["GET", "POST"])
def signup():
    errors = ""
    if "username" in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username")
        displayname = request.form.get("displayname")
        emailid = request.form.get("emailid")
        location = request.form.get("location")
        pwd1 = request.form.get("pwd1")
        pwd2 = request.form.get("pwd2")
        redo = False
        if pwd1 != pwd2:
            redo = True
            errors += "Passwords do not match. "
        sql = "SELECT * FROM users WHERE username = '{0}'".format(username)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) != 0:
            redo = True
            errors += "Username already exists. "
        sql = "SELECT * FROM users WHERE email = '{0}'".format(emailid)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) != 0:
            redo = True
            errors += "Email ID is already in use."
        if redo:
            flash(errors)
            return render_template("signup.html", data = request.form)
        displayname = displayname.title()
        sql = """INSERT INTO users (username, displayname, email, password, location) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}")""".format(username, displayname, emailid, pwd1, location)
        cursor.execute(sql)
        connection.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template("signup.html", data = None)

@app.route("/enter", methods = ["POST"])
def make_entry():
    content = request.form.get("content")
    if len(content) > 200:
        flash("The length of your post is limited to 200 characters. Try again.")
        data = request.form
        session['data'] = data
        return redirect(url_for('index'))
    sentiment = analyze(content)
    username = session['username']
    likes = 0
    now = datetime.datetime.now()
    timestamp = now.strftime("%H:%M, %d-%m-%Y")
    sql = """INSERT INTO talks (username, text, timestamp, likes, sentiment) VALUES('{0}', "{1}", '{2}', {3}, {4})""".format(username, content, timestamp, likes, sentiment)
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("index"))

@app.route("/users/<username>", methods = ["GET"])
def show_user(username):
    if "username" not in session:
        flash("Login to view.")
        return redirect(url_for("login"))
    sql = "SELECT username, displayname, email, location FROM users WHERE username = '{0}'".format(username)
    cursor.execute(sql)
    data = cursor.fetchall()
    if len(data) == 0:
        flash("No such user exists.")
        return redirect(url_for('index'))
    sql = "SELECT * FROM talks WHERE username = '{0}' ORDER BY talkid desc".format(username)
    cursor.execute(sql)
    talks = cursor.fetchall()
    username = session["username"]
    return render_template("user.html", data = data[0], talks = talks, username=username)

@app.route("/talkspot/<int:talkid>", methods = ["GET", "POST"])
def show_talk(talkid):
    if "username" not in session:
        flash("Login to view.")
        return redirect(url_for("login"))
    sql = "SELECT * FROM talks WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    data = cursor.fetchall()
    if len(data) == 0:
        flash("No such talkspot exists.")
        return redirect(url_for('index'))
    sql = "SELECT * FROM comments WHERE talkid = {0} ORDER BY commentid desc".format(talkid)
    cursor.execute(sql)
    comments = cursor.fetchall()
    username = session["username"]
    if "comment" in session:
        fill = session['comment']
        session.pop("comment", None)
        return render_template("talkspot.html", data = data[0], comments = comments, fill = fill, username = username)
    return render_template("talkspot.html", data = data[0], comments = comments, fill = None, username = username)

@app.route("/entercomment/<int:talkid>", methods = ["POST"])
def enter_comment(talkid):
    if "username" not in session:
        flash("Login to comment.")
        return redirect(url_for("login"))
    content = request.form.get("content")
    if len(content) > 200:
        flash("The length of your comment is limited to 200 characters. Try again.")
        data = request.form
        session['comment'] = data
        return redirect(url_for('show_talk', talkid=talkid))
    sentiment = analyze(content)
    username = session["username"]
    sql = """INSERT INTO comments (username, talkid, text, likes, sentiment) VALUES ('{0}', {1}, "{2}", {3}, {4})""".format(username, talkid, content, 0, sentiment)
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for('show_talk', talkid=talkid))
    
@app.route("/addlikecmt/<commentid>", methods = ["GET"])
def like_comment(commentid):
    if "username" not in session:
        flash("Login to upvote.")
        return redirect(url_for("login"))
    sql = "SELECT * FROM likes WHERE type = {0} AND id = {1} AND username = '{2}'".format(1, commentid, session["username"])
    cursor.execute(sql)
    count = cursor.fetchall()
    sql = "SELECT likes, talkid from comments WHERE commentid = {0}".format(commentid)
    cursor.execute(sql)
    likes = cursor.fetchall()
    talkid = likes[0][1]
    likes = likes[0][0]
    if len(count) != 0:
        flash("Can be upvoted only once.")
        return redirect(url_for("show_talk", talkid = talkid))
    sql = "UPDATE comments SET likes = {0} WHERE commentid = {1}".format(likes + 1, commentid)
    cursor.execute(sql)
    sql = "INSERT INTO likes (type, id, username) VALUES ({0}, {1}, '{2}')".format(1, commentid, session['username'])
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("show_talk", talkid = talkid))

@app.route("/addliketalk/<talkid>", methods = ["GET"])
def like_talk(talkid):
    if "username" not in session:
        flash("Login to upvote.")
        return redirect(url_for("login"))
    sql = "SELECT * FROM likes WHERE type = {0} AND id = {1} AND username = '{2}'".format(0, talkid, session["username"])
    cursor.execute(sql)
    count = cursor.fetchall()
    if len(count) != 0:
        flash("Can be upvoted only once.")
        return redirect(url_for("index"))
    sql = "SELECT likes, username FROM talks WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    result = cursor.fetchall()
    likes = result[0][0]
    username = result[0][1]
    sql = "UPDATE talks SET likes = {0} WHERE talkid = {1}".format(likes + 1, talkid)
    cursor.execute(sql)
    sql = "INSERT INTO likes (type, id, username) VALUES ({0}, {1}, '{2}')".format(0, talkid, session['username'])
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("index"))

@app.route("/addliketalk1/<talkid>", methods = ["GET"])
def like_talk1(talkid):
    if "username" not in session:
        flash("Login to upvote.")
        return redirect(url_for("login"))
    sql = "SELECT * FROM likes WHERE type = {0} AND id = {1} AND username = '{2}'".format(0, talkid, session["username"])
    cursor.execute(sql)
    count = cursor.fetchall()
    sql = "SELECT likes, username FROM talks WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    result = cursor.fetchall()
    likes = result[0][0]
    username = result[0][1]
    if len(count) != 0:
        flash("Can be upvoted only once.")
        return redirect(url_for("show_user", username=username))
    sql = "UPDATE talks SET likes = {0} WHERE talkid = {1}".format(likes + 1, talkid)
    cursor.execute(sql)
    sql = "INSERT INTO likes (type, id, username) VALUES ({0}, {1}, '{2}')".format(0, talkid, session['username'])
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("show_user", username=username))

@app.route("/addliketalk2/<talkid>", methods = ["GET"])
def like_talk2(talkid):
    if "username" not in session:
        flash("Login to upvote.")
        return redirect(url_for("login"))
    sql = "SELECT * FROM likes WHERE type = {0} AND id = {1} AND username = '{2}'".format(0, talkid, session["username"])
    cursor.execute(sql)
    count = cursor.fetchall()
    if len(count) != 0:
        flash("Can be upvoted only once.")
        return redirect(url_for("show_talk", talkid=talkid))
    sql = "SELECT likes, username FROM talks WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    result = cursor.fetchall()
    likes = result[0][0]
    username = result[0][1]
    sql = "UPDATE talks SET likes = {0} WHERE talkid = {1}".format(likes + 1, talkid)
    cursor.execute(sql)
    sql = "INSERT INTO likes (type, id, username) VALUES ({0}, {1}, '{2}')".format(0, talkid, session['username'])
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("show_talk", talkid=talkid))

@app.route("/search", methods=["GET", "POST"])
def search():
    if "username" not in session:
        flash("Login to Search.")
        return redirect(url_for("index"))
    searchtext = request.form.get("search_text")
    sql = "SELECT * FROM users WHERE username LIKE '%{0}%' OR displayname LIKE '%{0}%'".format(searchtext)
    cursor.execute(sql)
    result = cursor.fetchall()
    username = session["username"]
    return render_template("search.html", users=result, username=username)


if __name__ == "__main__":
    app.run()
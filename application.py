from flask import *
import requests
from flask import *
import pymysql
import datetime

app = Flask(__name__)
app.secret_key = "secret key"

connection = pymysql.connect(host="localhost", user="root", passwd="", database="talkspot")
cursor = connection.cursor()

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    sql = "SELECT * FROM talks ORDER BY talkid desc LIMIT 10;"
    cursor.execute(sql)
    recents = cursor.fetchall()
    if 'data' in session:
        data = session['data']
        session.pop('data', None)
        return render_template("homepage.html", data = data, recents = recents)
    return render_template("homepage.html", data = None, recents = recents)

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
            flash("Passwords do not match.")
        sql = "SELECT * FROM users WHERE username = '{0}'".format(username)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) != 0:
            redo = True
            flash("Username already exists.")
        sql = "SELECT * FROM users WHERE email = '{0}'".format(emailid)
        cursor.execute(sql)
        result = cursor.fetchall()
        if len(result) != 0:
            redo = True
            flash("Email ID is already in use.")
        if redo:
            return render_template("signup.html", data = request.form)
        sql = "INSERT INTO users (username, displayname, email, password, location) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(username, displayname, emailid, pwd1, location)
        cursor.execute(sql)
        connection.commit()
        session['username'] = username
        return redirect(url_for('index'))
    return render_template("signup.html", data = None)

@app.route("/enter", methods = ["POST"])
def make_entry():
    content = request.form.get("content")
    if len(content) > 20:
        flash("The length of your post is limited to 200 characters. Try again.")
        data = request.form
        session['data'] = data
        return redirect(url_for('index'))
    username = session['username']
    likes = 0
    now = datetime.datetime.now()
    timestamp = now.strftime("%H:%M, %d-%m-%Y")
    sql = "INSERT INTO talks (username, text, timestamp, likes) VALUES('{0}', '{1}', '{2}', {3});".format(username, content, timestamp, likes)
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("index"))

@app.route("/users/<username>", methods = ["GET"])
def show_user(username):
    sql = "SELECT displayname, email, location FROM users WHERE username = '{0}'".format(username)
    cursor.execute(sql)
    data = cursor.fetchall()
    if len(data) == 0:
        flash("No such user exists.")
        return redirect(url_for('index'))
    sql = "SELECT * FROM talks WHERE username = '{0}'".format(username)
    cursor.execute(sql)
    talks = cursor.fetchall()
    return render_template("user.html", data = data[0], talks = talks)

@app.route("/talkspot/<int:talkid>", methods = ["GET", "POST"])
def show_talk(talkid):
    sql = "SELECT * FROM talks WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    data = cursor.fetchall()
    if len(data) == 0:
        flash("No such talkspot exists.")
        return redirect(url_for('index'))
    sql = "SELECT * FROM comments WHERE talkid = {0}".format(talkid)
    cursor.execute(sql)
    comments = cursor.fetchall()
    if "comment" in session:
        fill = session['comment']
        session.pop("comment", None)
        return render_template("talkspot.html", data = data[0], comments = comments, fill = fill)
    return render_template("talkspot.html", data = data[0], comments = comments, fill = None)

@app.route("/entercomment/<int:talkid>", methods = ["POST"])
def enter_comment(talkid):
    content = request.form.get("content")
    if len(content) > 20:
        flash("The length of your comment is limited to 200 characters. Try again.")
        data = request.form
        session['comment'] = data
        return redirect(url_for('show_talk', talkid=talkid))
    sql = "INSERT INTO comments (talkid, text, likes) VALUES ({0}, '{1}', {2})".format(talkid, content, 0)
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for('show_talk', talkid=talkid))
    
if __name__ == "__main__":
    app.run()
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
    return render_template("homepage.html", data = None)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if "username" in session:
        return render_template("homepage.html", data = None)
    if request.method == "POST":
        username = request.form.get("username")
        pwd = request.form.get("pwd")
        sql = "SELECT * FROM users WHERE username = '{0}' AND password = '{1}';".format(username, pwd)
        cursor.execute(sql)
        rows = cursor.fetchall()
        if len(rows) == 1:
            session['username'] = username
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout", methods = ["GET"])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/enter", methods = ["POST"])
def make_entry():
    content = request.form.get("content")
    if len(content) > 20:
        flash("The length of your post is limited to 200 characters")
        data = request.form
        return render_template("homepage.html", data = data)
    username = session['username']
    likes = 0
    now = datetime.datetime.now()
    timestamp = now.strftime("%H:%M, %d-%m-%Y")
    sql = "INSERT INTO talks (username, text, timestamp, likes) VALUES('{0}', '{1}', '{2}', {3});".format(username, content, timestamp, likes)
    cursor.execute(sql)
    connection.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()
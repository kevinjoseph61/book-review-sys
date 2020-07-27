import os, json
from flask import Flask, session, redirect, render_template, request, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from datetime import datetime

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#database connnection from DATABASE_URL ensure that you create variable
engine = create_engine(os.environ.get('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

#decorater for login access pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#main page with search bar
@app.route("/")
@login_required
def index():
    return render_template("index.html")

#login page
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    username = request.form.get("username")
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html", message="You must provide a username!",back="login")
        elif not request.form.get("password"):
            return render_template("error.html", message="You must provide a password!",back="login")
        rows = db.execute("SELECT * FROM users WHERE username = :username", {"username": username.lower()})
        result = rows.fetchone()
        if result == None or not check_password_hash(result[1], request.form.get("password")):
            return render_template("error.html", message="An incorrect username/password was detected!",back="login")
        session["username"] = result[0]
        return redirect("/")
    else:
        return render_template("login.html")

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():   
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("error.html", message="You must provide a username!",back="register")
        userCheck = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":request.form.get("username").lower()}).fetchone()
        if userCheck:
            return render_template("error.html", message="Sorry, that username already exists!",back="register")
        elif not request.form.get("password"):
            return render_template("error.html", message="Please provide password!",back="register")
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="Please confirm your passoword!",back="register")
        elif not request.form.get("password") == request.form.get("confirmation"):
            return render_template("error.html", message="The passwords do not match!",back="register")
        hashedPassword = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            {"username":request.form.get("username"), 
                             "password":hashedPassword})
        db.commit()
        return render_template("info.html", message="Your account has been created!",back="login", back_place="to the login page!")
        return redirect("/login")
    else:
        return render_template("register.html")

#search
@app.route("/search", methods=["GET"])
@login_required
def search():
    if not request.args.get("book"):
        return render_template("error.html", message="Please query a book before clicking on search!", back="/")
    searchby = request.args.get("searchby")
    query = "%" + request.args.get("book") + "%"
    query = query.title()
    if searchby=="all":
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :query OR title LIKE :query OR author LIKE :query",{"query": query})
    elif searchby=="isbn":
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE isbn LIKE :query",{"query": query})
    elif searchby=="title":
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE title LIKE :query",{"query": query})
    else:
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE author LIKE :query",{"query": query})
    num = rows.rowcount
    if num == 0:
        return render_template("info.html", message="Sorry, there are no books which match your query!", back="/", back_place="back to the search page")
    books = rows.fetchall()
    return render_template("results.html", books=books, num=num, searchby=searchby.title())

#book page for reviews
@app.route("/book/<isbn>", methods=['GET','POST'])
@login_required
def book(isbn):
    if request.method == "POST":
        currentUser = session["username"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        row2 = db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn",
                    {"username": currentUser,
                     "isbn": isbn})
        if row2.rowcount == 1:
            return render_template("error.html",message='You already submitted a review for this book!', back="/book/"+isbn)
        rating = int(rating)
        time=str(datetime.now()).split('.')[0]
        db.execute("INSERT INTO reviews (username, isbn, review, rating, time) VALUES (:username, :isbn, :comment, :rating, to_timestamp(:time, 'yyyy-mm-dd hh24:mi:ss'))",
                    {"username": currentUser, 
                    "isbn": isbn, 
                    "comment": comment, 
                    "rating": rating,
                     "time": time})
        db.commit()
        return render_template("info.html", message="Your review has been posted!",back="/book/"+isbn, back_place="back to the book page!")
        return redirect("/book/" + isbn)
    else:
        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})
        bookInfo = row.fetchall()
        key = os.environ.get('GOODREADS_API_KEY')
        query = requests.get("https://www.goodreads.com/book/review_counts.json",
                params={"key": key, "isbns": isbn})
        response = query.json()
        response = response['books'][0]
        bookInfo.append(response)
        avg = db.execute("SELECT AVG(rating) from reviews WHERE isbn = :isbn",{"isbn": isbn}).fetchone()[0]
        if avg:
            avg=round(avg,2)
        results = db.execute("SELECT username, review, rating, to_char(time, 'DD Mon YY - HH24:MI:SS') as time from reviews WHERE isbn = :isbn ORDER BY time",
                            {"isbn": isbn})
        reviews = results.fetchall()
        return render_template("book.html", bookInfo=bookInfo, reviews=reviews, avg=avg)

#API route
@app.route("/api/<isbn>", methods=['GET'])
def api_call(isbn):
    row = db.execute("SELECT title, author, year, isbn from books WHERE isbn = :isbn;",
                    {"isbn": isbn})
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN/ Not found"}), 404
    tmp = row.fetchone()
    result = dict(tmp.items())
    rev = db.execute("SELECT isbn, count(*) as review_count, avg(rating) as average_score from reviews WHERE isbn = :isbn group by isbn;",
                    {"isbn": isbn})
    if rev.rowcount==0:
        result['average_score']=None
        result['review_count']=None
    else:
        result.update(dict(rev.fetchone().items()))
        result['average_score'] = float('%.2f'%(result['average_score']))
    return jsonify(result)

from flask import Flask, session, render_template, redirect, request, g
from flask_caching import Cache
from flask_session import Session
from tempfile import mkdtemp

from helpers import error, login_required, rowput, datalyze
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

# Configure app
app = Flask(__name__)
# Reloads templates when a file changes
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configures session
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Sets up simple caching
# cache = Cache()
# app.config["CACHE_TYPE"] = "simple"
# cache.init_app(app)

# Caching disabled
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Connects database to flask
DATABASE = "C:\\Users\\Jonathan Zhang\\Desktop\\Jonathan\\GitHub\\cs50_final_project\\budget_me\\budget.db"
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Dashboard page
@app.route("/")
@login_required
def index():
    # Opens database
    db = get_db()
    crsr = db.cursor()
    # Gets all purchases of user
    purchases = crsr.execute("SELECT * FROM purchases ORDER BY time DESC, category;").fetchall()
    print(rowput(purchases))

    categoryChart, methodChart = datalyze(purchases)

    return render_template("index.html", purchases=rowput(purchases), categoryChart=categoryChart, methodChart=methodChart)

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    # Clears existing session["user_id"]
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    else:
        # Validates username entry
        username = request.form.get("username")
        if not username:
            return error("Please enter a valid username.", 403)
        # Validates password entry
        password = request.form.get("password")
        if not password:
            return error("Please enter a valid password.", 403)

        # Opens database
        db = get_db()
        crsr = db.cursor()
        # Gets password hash and id
        user = crsr.execute("SELECT hash, id FROM users WHERE username=?;", username).fetchall()
        ### print(rowput(user))

        # Validates username and password
        if len(user) == 0:
            return error("Invalid username or password.")
        elif len(user) != 1:
            return error("Development error. Please contact support.")
        elif not check_password_hash(user[0][0], password):
            return error("Invalid username or password.")
        
        # Stores id of user in session (logged in)
        session["user_id"] = user[0][1]
        return redirect("/")

# Logout path
@app.route("/logout", methods=["GET"])
def logout():
    # Clears existing session["user_id"]
    session.clear()
    return redirect("/")

# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Opens database
        db = get_db()
        crsr = db.cursor()

        # Validates username entry and uniqueness
        username = request.form.get("username")
        unique = crsr.execute("SELECT id FROM users WHERE username=?;", username).fetchall()
        if not username:
            return error("Please enter a valid username.", 403)
        elif unique:
            return error("Sorry, that username is taken.")
        # Validates password entry and confirmation
        password = request.form.get("password1")
        confirmation = request.form.get("password2")
        if not password or not confirmation or password != confirmation:
            return error("Please enter a password and confirm it.", 403)

        # Registers user into database
        crsr.execute("INSERT INTO users (username, hash) VALUES (?,?);", (username, generate_password_hash(password)))
        db.commit()

        return render_template("login.html")

# Add a purchase
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_purchase():
    if request.method == "GET":
        return render_template("add_purchase.html")
    else:
        title = request.form.get("title")
        amount = request.form.get("amount") # required
        category = request.form.get("category") # required
        method = request.form.get("method") # required
        date = request.form.get("date") # required
        note = request.form.get("note")

        # Opens database
        db = get_db()
        crsr = db.cursor()
        # Inserts purchase into database
        crsr.execute("INSERT INTO purchases (title, amount, category, method, time, note, user_id) VALUES (?,?,?,?,?,?,?);", (title, amount, category, method, date, note, session["user_id"]))
        db.commit()

        return render_template("success.html", status="added")

# Edit an existing purchase
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit_purchase():
    if request.method == "GET":
        # Opens database
        db = get_db()
        crsr = db.cursor()
        # Retrieves recent month's purcahses from database
        purchases = crsr.execute("SELECT * FROM purchases WHERE time BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime');").fetchall()
        ### print(rowput(purchases))

        return render_template("edit_purchase.html", purchases=rowput(purchases))
        #return error("todo", 501)
    else:
        ident = request.form.get("purchase_id")
        ### print(ident)
        title = request.form.get("title")
        amount = request.form.get("amount") # required
        category = request.form.get("category") # required
        method = request.form.get("method") # required
        date = request.form.get("date") # required
        note = request.form.get("note")

        # Opens database
        db = get_db()
        crsr = db.cursor()
        # Updates purchase information with new fields
        crsr.execute("UPDATE purchases SET title=?, amount=?, category=?, method=?, time=?, note=? WHERE id=?;", (title, amount, category, method, date, note, ident))
        db.commit()

        return render_template("success.html", status="edited")

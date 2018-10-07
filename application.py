from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from collections import Counter
import json

from helpers import apology, login_required
from random import *

# Configure application
app = Flask(__name__)


# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///courses50.db")


@app.route("/")
@login_required
def index():
    """Show option to start test."""

    if request.method == "GET":
        # Show start test
        return render_template("index.html")

    if request.method == "POST":
        return render_template("test.html")


@app.route("/test", methods=["GET", "POST"])
@login_required
def test():
    """Show series of test questions"""

    # For the first test page.
    if request.method == "GET":

        # Start counter for the number of submissions made/questions answered in this test.
        global counter
        counter = 0
        # Define variable for the the total number of courses in the database.
        courses_total = 15426

        # Randomize through all courses by choosing a random course id number from total courses.
        while True:
            rand_1 = randint(1, courses_total)
            rand_2 = randint(1, courses_total)
            rand_3 = randint(1, courses_total)
            rand_4 = randint(1, courses_total)


            # Select the four random courses from the database
            selectedcourses = db.execute("SELECT * FROM courses WHERE (id=:rand_1 OR id=:rand_2 OR id=:rand_3 OR id=:rand_4)",
                                                                    rand_1=rand_1, rand_2=rand_2, rand_3=rand_3, rand_4=rand_4)
            # Choose to display only 4 courses.
            if len(selectedcourses) == 4:
                break

        # Pass through our selected courses to the code
        return render_template("test.html", selectedcourses=selectedcourses)

    # For all following test pages.
    if request.method == "POST":

        if request.form.get("favourite") != "NULL":
            # Add one to the counter for how many questions answered in test.
            counter += 1

            # Insert each selected course into database.
            db.execute("INSERT INTO users_courses (user_id, course_id) VALUES (:user_id, :course_id)",
                       user_id=session["user_id"], course_id=(request.form.get("favourite")))

        # Keep doing this whilst counter is less than the number of questions we want to ask
        if (counter < 15):

            courses_total = 15426
            while True:
                rand_1 = randint(1, courses_total)
                rand_2 = randint(1, courses_total)
                rand_3 = randint(1, courses_total)
                rand_4 = randint(1, courses_total)


                # Select the four random courses from the database
                selectedcourses = db.execute("SELECT * FROM courses WHERE (id=:rand_1 OR id=:rand_2 OR id=:rand_3 OR id=:rand_4)",
                                                                        rand_1=rand_1, rand_2=rand_2, rand_3=rand_3, rand_4=rand_4)

                if len(selectedcourses) == 4:
                    break

            return render_template("test.html", selectedcourses=selectedcourses)

        # If we have already answered the needed number of courses, execute result
        else:
            depts_chosen = db.execute("SELECT departments.short_name FROM departments \
                             JOIN courses ON courses.department_id = departments.id \
                             JOIN users_courses ON users_courses.course_id = courses.id \
                             WHERE users_courses.user_id=:id", id=session["user_id"])

            # Count number of occurences of each department chosen, and store in a list called 'departmentsliked'.
            departmentsliked = []
            for dept in depts_chosen:
                departmentsliked.append(dept["short_name"])

            # Use a mode a function that returns the most frequently selected concentration -- adapted from
            # https://stackoverflow.com/questions/36516279/how-to-return-elements-with-the-highest-occurrence-in-list
            def mode(list):
                ct = Counter(list)
                if not ct:
                    return apology("Must first take test", 400)
                max_value = max(ct.values())
                return sorted(key for key, value in ct.items() if value == max_value)

            # Select the highest occuring department and name it "concentration"
            concentration = mode(departmentsliked)[0]

            # Use Counter in Python to output list of suggestions, with key/value pairs for each department.
            suggestions = dict(Counter(departmentsliked))
            suggestions = json.dumps(suggestions)

            counter = 0
            return render_template("result.html", suggestions=suggestions, concentration=concentration)


@app.route("/result")
@login_required
def result():
    """Show result"""
    depts_chosen = db.execute("SELECT departments.short_name FROM departments \
                             JOIN courses ON courses.department_id = departments.id \
                             JOIN users_courses ON users_courses.course_id = courses.id \
                             WHERE users_courses.user_id=:id", id=session["user_id"])

    # Count number of occurences of each department chosen, and store in a list called 'departmentsliked'.
    departmentsliked = []
    for dept in depts_chosen:
        departmentsliked.append(dept["short_name"])

    # Define a function called mode that returns the most frequently selected concentration
    def mode(list):
        ct = Counter(list)
        if not ct:
            return apology("Must first take test", 400)
        max_value = max(ct.values())
        return sorted(key for key, value in ct.items() if value == max_value)
    # Select the highest occuring department and name it "concentration"
    concentration = mode(departmentsliked)[0]

    # Use Counter in Python to output list of suggestions, with key/value pairs for each department.
    suggestions = dict(Counter(departmentsliked))
    suggestions = json.dumps(suggestions)

    counter = 0
    return render_template("result.html", suggestions=suggestions, concentration=concentration)


@app.route("/history")
@login_required
def history():
    """Show history of course selections"""

    # Select the dictionary of all that the users have selected throughout the test
    history = db.execute("SELECT courses.id, courses.title, courses.description, courses.department_id, users_courses.starred,\
                        departments.short_name FROM courses JOIN users_courses ON courses.id = users_courses.course_id \
                        JOIN departments ON departments.id = courses.department_id \
                        WHERE users_courses.user_id=:id", id=session["user_id"])

    # Count number of occurences of each department chosen, and store in a list called 'departmentsliked'.
    departmentsliked = []
    for dept in history:
        departmentsliked.append(dept["short_name"])

    # Define a function called mode that returns the most frequently selected concentration
    def mode(list):
        ct = Counter(list)
        if not ct:
            return apology("Must first take test", 400)
        max_value = max(ct.values())
        return sorted(key for key, value in ct.items() if value == max_value)

    # Select the highest occuring department and name it "concentration"
    concentration = mode(departmentsliked)[0]

    # Select the id that matches your highest occuring concentration. More than one id can correspond to the same concentration
    dept_id = db.execute("SELECT id FROM departments WHERE short_name=:concentration", concentration=concentration)

    return render_template("history.html", history=history, dept_id=dept_id)

@app.route("/star", methods=["GET", "POST"])
@login_required
def star():
    """Stars specific courses if you want to take them later"""

    if request.method == "POST":
        courseid = int(request.form.get("starredcourse"))

        # Lookup whether it is starred or not.
        starlookup = db.execute("SELECT starred FROM users_courses WHERE course_id=:courseid AND user_id=:id", courseid=courseid, id=session["user_id"])
        starboolean = int(starlookup[0]["starred"])
            # If starred, unstar.
        if starboolean == 1:
            db.execute("UPDATE users_courses SET starred=0 WHERE course_id=:courseid AND user_id=:id", courseid=courseid, id=session["user_id"])
        # If unstarred, star.
        else:
            db.execute("UPDATE users_courses SET starred=1 WHERE course_id=:courseid AND user_id=:id", courseid=courseid, id=session["user_id"])

        # Select the courses from database that user has starred
        starredcourses = db.execute("SELECT courses.title, courses.description, departments.short_name, courses.id FROM courses JOIN users_courses ON courses.id = users_courses.course_id \
                                    JOIN departments ON departments.id = courses.department_id \
                                    WHERE users_courses.starred=1 AND users_courses.user_id=:id", id=session["user_id"])

        return render_template("star.html", starredcourses=starredcourses)

    if request.method == "GET":

        # # Select the courses from database that user has starred
        starredcourses = db.execute("SELECT courses.title, courses.description, departments.short_name, courses.id FROM courses JOIN users_courses ON courses.id = users_courses.course_id \
                                    JOIN departments ON departments.id = courses.department_id \
                                    WHERE users_courses.starred=1 AND users_courses.user_id=:id", id=session["user_id"])
        return render_template("star.html", starredcourses=starredcourses)



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
        rows = db.execute("SELECT * FROM users WHERE username=:username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

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

@app.route("/about")
def about():
    """Display about template"""

    # Display paragraph about website and group
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure a username was submitted
        if not request.form.get("username"):
            return apology("Must provide username", 400)

        # Ensure a password is submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 400)

        # Ensure a confirmation password is submitted
        elif not request.form.get("confirmation"):
            return apology("Must provide password again", 400)

        # If it's not the same.
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("Both passwords must match", 400)

        # Store hash value to protect password.
        hashed = generate_password_hash(request.form.get("password"))

        # Add user to database.
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                          username=request.form.get("username"), hash=hashed)

        # Check the user doesn't already exist.
        if not rows:
            return apology("User already exists", 400)

        # Remember which user has logged in.
        session["user_id"] = rows

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

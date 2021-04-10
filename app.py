import sqlite3
# required imports; you may add more in the future; currently, we will only use render_template
from flask import Flask, render_template, request, g, session, redirect, url_for, escape, send_file, send_from_directory

DATABASE = './assignment3.db'

# tells Flask that "this" is the current running app
app = Flask(__name__)
app.secret_key = 'admin'


# setup the default route
# this is the page the site will load by default (i.e. like the home page)


def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
# (don't worry if you don't understand this code)


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# given a query, executes and returns the result
# (don't worry if you don't understand this code)


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()


@ app.route('/')
def root():
    # tells Flask to render the HTML page called index.html
    return render_template('brilliant.html')
    # if 'username' in session:
    #     # print(isInstructor())
    #     return render_template('index.html', username=session['username'], isInstructor=isInstructor())
    # return redirect(url_for("login"))


@ app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sql = """
			SELECT *
            FROM Students
            UNION
            SELECT * FROM Instructors
			"""
        results = query_db(sql, args=(), one=False)
        for result in results:
            if result[0] == request.form['username']:
                if str(result[1]) == str(request.form['password']):
                    session['username'] = request.form['username']
                    return redirect(url_for('root'))
        return render_template('login.html', incorrect=True)
    elif 'username' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', incorrect=False)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@ app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')


def isInstructor():
    db = get_db()
    res_query = query_db(
        'select * from Instructors where username = ?', [str(session['username'])], one=True)
    db.close()
    return res_query != None


@ app.route('/remarks', methods=['GET'])
def remark():
    if 'username' in session:
        db = get_db()
        db.row_factory = make_dicts
        # make a new cursor from the database connection
        cur = db.cursor()
        remarks = []
        res_query = query_db(
            'select username, test, reason from Remarks', one=False)
        for request in res_query:
            remarks.append(request)
        sql = """ SELECT first_name, last_name FROM Students WHERE username = ? UNION SELECT first_name, last_name FROM Instructors WHERE username = ? """
        res_query = query_db(sql, args=(
            [str(session['username']), str(session['username'])]), one=True)
        # full_name = res_query["first_name"][0].upper() + res_query["first_name"][1:] + \
        #                                              " " + \
        #                                                  res_query["last_name"][0].upper(
        #                                                  ) + res_query["last_name"][1:]
        db.commit()
        cur.close()
        db.close()
        return render_template('remarks.html', full_name="full_name", remarks=remarks, username=session['username'], isInstructor=isInstructor)
    return redirect(url_for("login"))


@ app.route('/home')
def home():
    # tells Flask to render the HTML page called index.html
    if 'username' in session:
        return redirect(url_for("root"))
    return redirect(url_for("login"))


@ app.route('/assignments')
def assignments():
    # tells Flask to render the HTML page called index.html

    if 'username' in session:
        return render_template('assignments.html', username=session['username'])
    return redirect(url_for("login"))


@ app.route('/team')
def team():
    # tells Flask to render the HTML page called index.html
    if 'username' in session:
        return render_template('team.html', username=session['username'], isInstructor=isInstructor())
    return redirect(url_for("login"))


@ app.route('/syllabus')
def syllabus():
    if 'username' in session:
        return render_template('syllabus.html', username=session['username'])
    return redirect(url_for("login"))


@ app.route('/grades')
def grades():
    if 'username' in session:
        db = get_db()
        db.row_factory = make_dicts
        # make a new cursor from the database connection
        cur = db.cursor()

        grades = []

        res_query = query_db(
            'select * from Instructors where username = ?', [str(session['username'])], one=True)

        if res_query == None:
            isInstructor = False
            res_query = query_db(
                'select * from Grades where username = ?', [str(session['username'])], one=True)

            # If the student just created an account insert new mark info
            if res_query == None:
                cur.execute('insert into Grades (username, quiz, quiz2, midterm, exam) values (?, ?, ?, ?, ?)', [
                    str(session['username']),
                    None,
                    None,
                    None,
                    None
                ])

            # Get all information from grade table where it matches student username
            res_query = query_db(
                'select * from Grades where username = ?', [str(session['username'])], one=False)
            for student in res_query:
                grades.append(student)
        else:
            isInstructor = True
            res_query = query_db(
                'select * from Grades')
            for student in res_query:
                grades.append(student)

        sql = """
			SELECT first_name, last_name
            FROM Students
            WHERE username = ?
            UNION
            SELECT first_name, last_name FROM Instructors
            WHERE username = ?
			"""
        res_query = query_db(sql, args=(
            [str(session['username']), str(session['username'])]), one=True)
        full_name = res_query["first_name"][0].upper(
        ) + res_query["first_name"][1:] + " " + res_query["last_name"][0].upper() + res_query["last_name"][1:]

        db.commit()
        cur.close()
        db.close()
        return render_template('grades.html', student_grades=grades, full_name=full_name, isInstructor=isInstructor, username=session['username'])
    return redirect(url_for("login"))


@ app.route('/tests')
def tests():
    if 'username' in session:
        return render_template('tests.html', username=session['username'])
    return redirect(url_for("login"))


@ app.route('/dummypdf')
def dummypdf():
    if 'username' in session:
        return send_from_directory("static", 'dummy.pdf')
    return redirect(url_for("login"))


@ app.route('/feedback')
def feedback():
    if 'username' in session:
        db = get_db()
        db.row_factory = make_dicts
        # make a new cursor from the database connection
        cur = db.cursor()
        feedbacks = []
        res_query = query_db(
            'select * from Feedback', one=False)
        for request in res_query:
            feedbacks.append(request)
        sql = """ SELECT first_name, last_name FROM Students WHERE username = ? UNION SELECT first_name, last_name FROM Instructors WHERE username = ? """
        res_query = query_db(sql, args=(
            [str(session['username']), str(session['username'])]), one=True)
        db.commit()
        cur.close()
        db.close()
        return render_template('feedback.html', full_name="full_name", feedbacks=feedbacks, username=session['username'], isInstructor=isInstructor)
    return redirect(url_for("login"))


@ app.route('/sendfeedback')
def sendfeedback():
    if 'username' in session:
        return render_template("sendfeedback.html", username=session['username'])
    return redirect(url_for("login"))


@ app.route('/send-feedback', methods=["POST"])
def newfeedback():
    db = get_db()
    db.row_factory = make_dicts
    # make a new cursor from the database connection
    cur = db.cursor()
    data = request.form

    cur.execute('insert into Feedback (feedback) values (?)', [
        data['feedback'],
    ])

    db.commit()
    cur.close()
    db.close()
    return redirect((url_for("sendfeedback")))


@ app.route('/css/index/')
def css():
    return send_from_directory("static", 'index.css')


@ app.route('/remark-request', methods=['POST'])
def remark_request():
    db = get_db()
    db.row_factory = make_dicts
    # make a new cursor from the database connection
    cur = db.cursor()
    data = request.form
    print(data)
    cur.execute('insert into Remarks (username, test, reason) values (?, ?, ?)', [
        data['username'],
        data['test'],
        data['reason'],
    ])

    db.commit()
    cur.close()
    db.close()
    return redirect((url_for("grades")))


@ app.route('/change-grade', methods=['POST'])
def change_grade():
    db = get_db()
    db.row_factory = make_dicts
    # make a new cursor from the database connection
    cur = db.cursor()
    data = request.form
    print(data)
    cur.execute("UPDATE Grades SET " + data["test"] + "=? WHERE username=?",
                (data["new_value"], data["username"]))

    db.commit()
    cur.close()
    db.close()
    return redirect((url_for("grades")))


@ app.route('/new-user', methods=['POST'])
def new_student():
    db = get_db()
    db.row_factory = make_dicts
    # make a new cursor from the database connection
    cur = db.cursor()

    # get the post body
    user = request.form

    if user.get("instructor") != None:  # They are an instructor
        sql = """
                SELECT *
                FROM Instructors
                """
        userType = "Instructors"
    else:  # They are a student
        sql = """
                SELECT *
                FROM Students
                """
        userType = "Students"

    results = query_db(sql, args=(), one=False)
    for result in results:
        if result['username'] == user['username']:
            return render_template('signup.html', exists=True)

    if user.get("instructor") != None:  # They are an instructor
        # insert the new instructor into the database
        cur.execute('insert into Instructors (username, password, first_name, last_name) values (?, ?, ?, ?)', [
            user['username'],
            user['password'],
            user['first_name'],
            user['last_name'],
        ])
    else:  # They are a student
        # insert the new student into the database
        cur.execute('insert into Students (username, password, first_name, last_name) values (?, ?, ?, ?)', [
            user['username'],
            user['password'],
            user['first_name'],
            user['last_name'],
        ])
    # commit the change to the database
    db.commit()
    # close the cursor
    cur.close()

    return redirect(url_for('login'))


# run the app when app.py is run
if __name__ == '__main__':
    app.run()

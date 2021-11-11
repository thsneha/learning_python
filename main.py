from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

from configs.config import validate_api

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)import mysql.connector
app.secret_key = 'riya_app'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root123@123'
app.config['MYSQL_DB'] = 'flask'

# Intialize MySQL
mysql = MySQL(app)

PREFIX = "/v1"


# http://localhost:5000/v1/index
# http://localhost:5000/v1/
@app.route(PREFIX + '/index/<name>', methods=['GET'])
@app.route(PREFIX + '/<name>', methods=['GET'])
def index(name):
    api_key = validate_api(request)
    if api_key == 'python-login':
        return jsonify({"message": "OK: Your api_key is Authorized to access APIs", "name": name}), 200
    else:
        return jsonify({"message": "ERROR: Unauthorized, api_key is invalid"}), 401


@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        print("account:..", account)
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/pythonlogin/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'invalid email address'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'username contains only characters and numbers'
        elif not username or not password or not email:
            msg = 'please fillout the form'
        else:
            cursor.execute('INSERT into accounts VALUES(NULL,%s,%s,%s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'you have successfully registered'
    elif request.method == 'POST':
        msg = 'please out the form'
    return render_template('register.html', msg=msg)


@app.route(PREFIX + "/new_registration", methods=["POST"])
def new_registration():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        email = data["email"]
        print(data)
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = {"message": 'Account already exists!'}
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = {"message": 'Invalid email address!'}
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = {"message": 'Username must contain only characters and numbers!'}
        elif not username or not password or not email:
            msg = {"message": 'Please fill out the form!'}
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'

        return jsonify(msg)


@app.route(PREFIX + "/get_user")
def get_user():
    data = []
    if request.method == "GET":
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("select * from accounts")
        accounts = cursor.fetchall()
        print(type(accounts))
        for i in accounts:
            data.append(i["username"])
        resp = jsonify({'message': 'Extracted data successfully', 'reports': data})
        return resp


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/pythonlogin/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/pythonlogin/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

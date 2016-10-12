from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
app = Flask(__name__)
app.secret_key = 'thisisthekey'
mysql = MySQLConnector(app,'mydb')
bcrypt = Bcrypt(app)

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    # Test for login
    if not 'login' in session:
        session['login'] = False
    # If logged in, redirect to page
    if session['login']:
        return redirect('/wall')
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def create():
    # Get data
    data = {
        'first_name': request.form['first_name'],
        'last_name':  request.form['last_name'],
        'email': request.form['email'],
        'passworda': request.form['passworda'],
        'passwordb': request.form['passwordb'],
        'hashpass': ''
    }
    # Validation testing
    failboat = False
    if (len(data['first_name']) < 2):
        flash('First name must be at least 2 characters.')
        failboat = True
    if (len(data['last_name']) < 2):
        flash('First name must be at least 2 characters.')
        failboat = True
    if not EMAIL_REGEX.match(data['email']):
        flash('Email is not valid. Please enter a valid email address.')
        failboat = True
    if len(data['email']) < 1:
        flash('Please enter a valid email address.')
        failboat = True
    if (len(data['passworda']) < 8 or len(data['passwordb']) < 8):
        flash('Password must be at least 8 characters')
        failboat = True
    if (data['passworda'] != data['passwordb']):
        flash('Passwords must match')
        failboat = True
    if failboat:
        return redirect('/')
    data['hashpass'] = bcrypt.generate_password_hash(data['passworda'])
    # Send query to database
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :hashpass, NOW(), NOW())"
    session['login'] = mysql.query_db(query, data)
    flash('Thanks for registering!')
    return redirect('/wall')

@app.route('/login', methods=['POST'])
def login():
    # Fetch user information and check password
    user = mysql.query_db("SELECT * FROM users WHERE email = '"+request.form['loginemail']+"'")
    if user:
        user = user[0]
    else:
        flash('Please enter a valid username and password.')
        return redirect('/')
    if bcrypt.check_password_hash(user['password'], request.form['loginpassword']):
        session['login'] = user['id']
        return redirect('/wall')
    else:
        flash('Please enter a valid username and password.')
        return redirect('/')

@app.route('/postmessage', methods=['POST'])
def message():
    # Fetch message data and insert into database
    data = {
        'message': request.form['message'],
        'users_id': session['login']
    }
    print data
    if len(data['message']) < 1:
        flash('Please enter a message.')
        return redirect('/wall')
    query = "INSERT INTO messages (message, users_id, created_at, updated_at) VALUES (:message, :users_id, NOW(), NOW())"
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/postcomment', methods=['POST'])
def comment():
    # Fetch comment data and insert into database
    data = {
        'comment': request.form['comment'],
        'messages_id': request.form['messages_id'],
        'users_id': session['login']
    }
    if len(data['comment']) < 1:
        flash('Please enter a comment.')
        return redirect('/wall')
    query = "INSERT INTO comments (comment, messages_id, users_id, created_at, updated_at) VALUES (:comment, :messages_id, :users_id, NOW(), NOW())"
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/wall')
def wall():
    # Render wall or redirect home if not logged in
    if not session['login']:
        flash('Please log in to view the wall.')
        return redirect('/')
    messages = mysql.query_db('SELECT users.first_name, users.last_name, messages.id, messages.message, messages.created_at FROM messages JOIN users ON users.id = messages.users_id ORDER BY messages.created_at desc')
    all_comments = mysql.query_db('SELECT users.first_name, users.last_name, comments.messages_id, comments.comment, comments.created_at FROM comments JOIN users on users.id = comments.users_id ORDER BY comments.created_at asc')
    user = mysql.query_db('SELECT * FROM users WHERE id = '+str(session['login']))
    return render_template('wall.html', all_messages = messages, all_comments = all_comments, user = user)

@app.route('/logout')
def logout():
    # Show logout message and clear session variable
    flash('You have been logged out.')
    session['login'] = False
    return redirect('/')

app.run(debug=True)

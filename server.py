from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import datetime
import re
app = Flask(__name__)
app.secret_key = 'shhhDontTell'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    mysql = connectToMySQL("user_wall")
    if 'logged_in' in session:
        welcome_message = "Welcome home " + session['first_name'] + "!"
    else:
        welcome_message = "Welcome home!"
    return render_template('index.html', welcome_message=welcome_message)

@app.route('/login')
def login():
    if 'logged_in' in session:
        name = session['first_name']
    else:
        name = ""
    return render_template('login.html', name=name)

@app.route('/validate_login', methods=['POST'])
def valdiate_login():
    mysql = connectToMySQL("user_wall")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = {
        'email': request.form['email']
    }
    if 'logged_in' in session:
        flash(u'You are already logged in!', 'login')
    else:
        login_attempt = mysql.query_db(query, data)
        if login_attempt:
            if bcrypt.check_password_hash(login_attempt[0]['password'], request.form['password']):
                session['userid'] = login_attempt[0]['user_id']
                return redirect('/success')
        flash(u'You could not be logged in. Please make sure that your email and password are correct!', 'login')
    return redirect('/login')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/success')
def success():
    mysql = connectToMySQL("user_wall")
    query = "SELECT * FROM users WHERE user_id=%(userid)s;"
    data = {
        'userid': session['userid']
    }
    logged_in = mysql.query_db(query, data)
    for user in logged_in:
        session['user_id'] = user['user_id']
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        session['email'] = user['email']

    first_name = session['first_name']
    session['logged_in'] = True
    return render_template('success.html', name=first_name)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/validate_registration', methods=['POST'])
def validate_registration():
    mysql = connectToMySQL("user_wall")
    duplicate_validation = mysql.query_db("SELECT email FROM users")
    count = 0
    upper = 0
    lower = 0
    duplicate = ""
    # Check email #
    for email in duplicate_validation:
        if request.form['email'] == email['email']:
            duplicate = email['email']
    if len(request.form['email']) < 1:
        flash(u'Email is required!', 'email')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash(u'Invalid email!', 'email')
    elif request.form['email'] == duplicate:
        flash(u'The email ' + request.form['email'] + ' is already registered!', 'email')
    else:
        count += 1
        session['email'] = request.form['email']
    # Check first name#
    if len(request.form['first_name']) < 1:
        flash(u'First Name is required!', 'first_name')
    elif str.isalpha(request.form['first_name']) == False:
        flash(u'First Name must contain only alphanumeric characters!', 'first_name')
    else:
        count += 1
        session['first_name'] = request.form['first_name']
    # Check last name #
    if len(request.form['last_name']) < 1:
        flash(u'Last Name is required!', 'last_name')
    elif str.isalpha(request.form['last_name']) == False:
        flash(u'Last Name must contain only alphanumeric characters!', 'last_name')
    else:
        count += 1
        session['last_name'] = request.form['last_name']
    # check password #
    if len(request.form['password']) < 1:
        flash(u'Password is required!', 'password')
    elif len(request.form['password']) >= 1 and len(request.form['password']) < 8:
        flash(u'Password must be longer thant 8 characters!', 'password')
    else:
        count += 1
    # verify password has one upper and lower case letter #
    if len(request.form['password']) >= 1 and len(request.form['password']) >= 8:
        for x in request.form['password']:
            if str.islower(x) == True:
                lower+=1
            if str.isupper(x) == True:
                upper+=1
        print(upper,lower)
        if lower > 0 and upper > 0:
            count+=1
        else:
            flash(u'Password must both an upper case and lower case character!', 'password')
        # verify password #
    if request.form['password_confirm'] != request.form['password']:
        flash(u'Your password confirmation must match your password!', 'password')
    else:
        count += 1
        session['password_confirm'] = request.form['password_confirm']
    if count == 6:
        session['first_name'] = request.form['first_name']
        session['last_name'] = request.form['last_name']
        session['email'] = request.form['email']
        session['password'] = bcrypt.generate_password_hash(request.form['password'])
        return redirect('/create_user')
    else:
        return redirect('/registration')

@app.route('/create_user')
def create_user():
    mysql = connectToMySQL("user_wall")
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUEs (%(first_name)s, %(last_name)s, %(email)s, %(password)s, NOW(), NOW());"
    data = {
        'first_name': session['first_name'],
        'last_name': session['last_name'],
        'email': session['email'],
        'password': session['password']
    }
    new_user_id = mysql.query_db(query, data)
    session['logged_in'] = True
    return redirect('/registration_success')

@app.route('/registration_success')
def registration_success():
    mysql = connectToMySQL("user_wall")
    query = "SELECT * FROM users WHERE email=%(userid)s;"
    data = {
        'userid': session['email']
    }
    logged_in = mysql.query_db(query, data)
    for user in logged_in:
        session['user_id'] = user['user_id']
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        session['email'] = user['email']
    first_name = session['first_name']
    session['logged_in'] = True
    return render_template('registration_success.html', name=first_name)

@app.route('/get_wall_data')
def get_wall_data():
    mysql = connectToMySQL("user_wall")
    wall_data = mysql.query_db("SELECT users.user_id, users.first_name, users.email, messages.message_id, messages.message, messages.recipient_id, messages.created_at, DATE_FORMAT(messages.created_at, '%m/%d/%Y') AS message_date, DATE_FORMAT(messages.created_at, '%h:%m %p') AS message_time, COUNT(messages.message_id) AS messages_sent, COUNT(messages.recipient_id) AS messages_received FROM users LEFT JOIN messages ON messages.user_id = users.user_id GROUP BY users.user_id ORDER BY messages.created_at DESC")
    if 'logged_in' in session:
        session['wall_data'] = wall_data
        return redirect('/wall')
    else:
        welcome_message_wall = "Please login to view your wall!"
        return render_template('wall.html', welcome_message_wall=welcome_message_wall)

@app.route('/wall')
def wall():
    mysql = connectToMySQL("user_wall")
    wall_posts = mysql.query_db("SELECT users.user_id, users.first_name, users.email, messages.message_id, messages.message, messages.recipient_id, messages.created_at, DATE_FORMAT(messages.created_at, '%m/%d/%Y') AS message_date, DATE_FORMAT(messages.created_at, '%h:%m %p') AS message_time, COUNT(messages.message_id) AS messages_sent, COUNT(messages.recipient_id) AS messages_received FROM users LEFT JOIN messages ON messages.user_id = users.user_id GROUP BY messages.message_id ORDER BY messages.created_at DESC")
    welcome_message_wall = "Welcome back, " + session['first_name'] + "!"
    name = session['first_name']
    wall_data = session['wall_data']
    return render_template('wall.html', welcome_message_wall=welcome_message_wall, name=name, wall_posts=wall_posts, wall_data=wall_data)

@app.route('/create_message', methods=['POST'])
def create_message():
    mysql = connectToMySQL("user_wall")
    query = "INSERT INTO messages (message, recipient_id,  user_id, created_at, updated_at) VALUEs (%(message)s, %(recipient_id)s, %(user_id)s, NOW(), NOW());"
    data = {
        'message': request.form['message'],
        'recipient_id': request.form['recipient_id'],
        'user_id': session['user_id']
    }
    new_message = mysql.query_db(query, data)
    return redirect('/wall')

if __name__=="__main__":
    app.run(debug=True)
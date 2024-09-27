from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import MySQLdb.cursors

app = Flask(__name__)

# Set the secret key for session management
app.secret_key = 'your_secret_key_here'  # Replace with a strong unique key

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'sticky_notes_app'

mysql = MySQL(app)

def is_logged_in():
    return 'loggedin' in session

@app.route('/')
def index():
    if is_logged_in():
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM notes WHERE user_id = %s', (user_id,))
        notes = cursor.fetchall()
        return render_template('index.html', notes=notes)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))  
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = sha256_crypt.hash(request.form['password'])

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
        mysql.connection.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))  
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and sha256_crypt.verify(password, user['password']):
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('login'))

@app.route('/add_note', methods=['POST'])
def add_note():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    note_id = request.form.get('note_id')
    note_text = request.form['note_text']
    note_color = request.form['note_color']
    user_id = session['id']

    cursor = mysql.connection.cursor()
    
    if note_id:  
        cursor.execute('UPDATE notes SET text = %s, color = %s WHERE id = %s AND user_id = %s',
                       (note_text, note_color, note_id, user_id))
    else:  
        cursor.execute('INSERT INTO notes (user_id, text, color) VALUES (%s, %s, %s)',
                       (user_id, note_text, note_color))
    
    mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM notes WHERE id = %s AND user_id = %s', (note_id, session['id']))
    mysql.connection.commit()
    return redirect(url_for('index'))

@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM notes WHERE id = %s AND user_id = %s', (note_id, session['id']))
    note = cursor.fetchone()

    if note:
        cursor.execute('SELECT * FROM notes WHERE user_id = %s', (session['id'],))
        notes = cursor.fetchall()
        return render_template('index.html', note_to_edit=note, notes=notes)
    return redirect(url_for('index'))  


@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)

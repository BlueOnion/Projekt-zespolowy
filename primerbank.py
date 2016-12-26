from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug import check_password_hash, generate_password_hash
import sqlite3

# database configuration
USERS = '/tmp/users.db'
PRIMERS = '/tmp/primers.db'
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

def get_db(database):
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config[database])
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

def query_db(database, query, args=(), one=False):
    cur = get_db(database).execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def check_user(email):
    rv = query_db('USERS', 'select email from users where email=?', [email], one=True)
    return rv[0] if rv else None

@app.before_request
def before_request():
    g.user = None
    if 'email' in session:
        g.user = query_db('USERS', 'select * from users where email=?', [session['email']], one=True)

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# searching primers / main site
@app.route('/')
def search_primers():
    return render_template('search_primers.html')

# registration system
@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('search_primers'))
    if request.method == 'POST':
        if not request.form['email'] or '@' not in request.form['email']:
            flash('Musisz podać poprawny adres email', 'error')
        elif not request.form['password']:
            flash('Musisz podać hasło', 'error')
        elif request.form['password'] != request.form['password2']:
            flash('Podane hasła muszą być identyczne', 'error')
        elif check_user(request.form['email']) is not None:
            flash('Konto o podanym adresie email już istnieje', 'error')
        else:
            db = get_db('USERS')
            db.execute('insert into users (email, password_hash) values (?, ?)',
                        [request.form['email'], generate_password_hash(request.form['password'])])
            db.commit()
            flash('Zostałeś zarejestrowany, teraz możesz się zalogować', 'message')
            return redirect(url_for('login'))
    return render_template('register.html')

# login system
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('search_primers'))
    if request.method == 'POST':
        user = query_db('USERS', 'select * from users where email=?', [request.form['email']], one=True)
        if (user is None) or not check_password_hash(user['password_hash'], request.form['password2']):
            flash('Błędna nazwa użytkownika lub hasło', 'error')
        else:
            session['email'] = user['email']
            flash('Zostałeś zalogowany', 'message')
            return redirect(url_for('search_primers'))
    return render_template('login.html')

# logout system
@app.route('/logout')
def logout():
    if 'user_id' not in session:
        abort(401)
    session.pop('email', None)
    flash('Zostałeś wylogowany', 'message')
    return redirect(url_for('search_primers'))

if __name__ == '__main__':
    app.run()

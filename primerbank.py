from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from werkzeug import check_password_hash, generate_password_hash
import sqlite3

# database configuration
DATABASE = '/tmp/primerbank.db'
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def check_user(email):
    rv = query_db('select email from users where email=?', [email], one=True)
    return rv[0] if rv else None

@app.before_request
def before_request():
    g.user = None
    if 'email' in session:
        g.user = query_db('select * from users where email=?', [session['email']], one=True)

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# szukanie primera (strona główna)
@app.route('/')
def search_primers():
    return render_template('search_primers.html')

# wyświetlanie primerów użytkownika
@app.route('/my_primers')
def my_primers():
    if 'email' not in session:
        abort(401)
    db = get_db()
    cur = db.execute('select pid, pname, psequence from primers where owner=? order by pid asc', [session['email']])
    primers = cur.fetchall()
    return render_template('my_primers.html', primers=primers)

# dodawanie nowego primera
@app.route('/add_primer', methods=['GET', 'POST'])
def add_primer():
    if 'email' not in session:
        abort(401)
    if request.method == 'POST':
        db = get_db()
        db.execute('insert into primers (pname, ptype, psequence, nt, temp_gen, temp_calc, owner) values (?,?,?,?,?,?,?)',
                    [request.form['pname'], request.form['ptype'], request.form['psequence'].upper(), request.form['nt'], request.form['temp_gen'], request.form['temp_calc'], session['email']])
        db.commit()
        flash('Nowy wpis został pomyślnie dodany', 'message')
        return redirect(url_for('my_primers'))
    return render_template('add_primer.html')

# edytowanie primera
@app.route('/edit_primer/<int:x>', methods=['GET', 'POST'])
def edit_primer(x):
    # odmowa dostępu w przypadku użytkownika niezalogowanego
    if 'email' not in session:
        abort(401)
    # odmowa dostępu w przypadku użytkownika zalogowanego nie będącego właścicielem
    else:
        primer = query_db('select * from primers where pid=?', [x,], one=True)
    if primer is None:
        abort(404)
    elif session['email'] != primer['owner']:
        abort(401)
    # właściwa funkcja
    db = get_db()
    cur = db.execute('select * from primers where pid=? and owner=?', [x, session['email']])
    primers = cur.fetchall()
    if request.method == 'POST':
        db.execute('update primers set pname=?, psequence=? where pid=?', [request.form['pname'], request.form['psequence'], x])
        db.commit()
        flash('Wpis został pomyślnie edytowany', 'message')
        return(redirect(url_for('my_primers')))
    return render_template('edit_primer.html', value=x, primers=primers)

# usuwanie primera
@app.route('/del_primer/<int:x>')
def del_primer(x):
    # odmowa dostępu w przypadku użytkownika niezalogowanego
    if 'email' not in session:
        abort(401)
    # odmowa dostępu w przypadku użytkownika zalogowanego nie będącego właścicielem
    else:
        primer = query_db('select * from primers where pid=?', [x,], one=True)
    if primer is None:
        abort(404)
    elif session['email'] != primer['owner']:
        abort(401)
    # właściwa funkcja
    db = get_db()
    db.execute('delete from primers where pid=? and owner=?', [x, session['email']])
    db.commit()
    flash('Wpis został pomyślnie usunięty', 'message')
    return redirect(url_for('my_primers'))

# system rejestracji
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
            db = get_db()
            db.execute('insert into users (email, password_hash) values (?, ?)',
                        [request.form['email'], generate_password_hash(request.form['password'])])
            db.commit()
            flash('Zostałeś zarejestrowany, teraz możesz się zalogować', 'message')
            return redirect(url_for('login'))
    return render_template('register.html')

# system logowania
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('search_primers'))
    if request.method == 'POST':
        user = query_db('select * from users where email=?', [request.form['email']], one=True)
        if (user is None) or not check_password_hash(user['password_hash'], request.form['password2']):
            flash('Błędna nazwa użytkownika lub hasło', 'error')
        else:
            session['email'] = user['email']
            flash('Zostałeś zalogowany', 'message')
            return redirect(url_for('search_primers'))
    return render_template('login.html')

# system wylogowywania
@app.route('/logout')
def logout():
    if 'email' not in session:
        abort(401)
    session.pop('email', None)
    flash('Zostałeś wylogowany', 'message')
    return redirect(url_for('search_primers'))

if __name__ == '__main__':
    app.run()

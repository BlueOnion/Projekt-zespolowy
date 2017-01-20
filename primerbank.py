from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response
from werkzeug import check_password_hash, generate_password_hash
import sqlite3
import pdfkit

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
@app.route('/', methods=['GET', 'POST'])
def search_primers():
    primers = ()
    if request.method == 'POST':
        primers = query_db('select * from primers where (pname=? or psequence=?) and owner!=? ', [request.form['query'], request.form['query'], session['email']])
        if not primers:
            flash('Nie znaleziono żadnego wpisu odpowiadającego podanym kryteriom', 'error')
    return render_template('search_primers.html', primers=primers)

# wyświetlanie primerów użytkownika
@app.route('/my_primers')
def my_primers():
    if 'email' not in session:
        abort(401)
    primers = query_db('select * from primers where owner=? order by pid asc', [session['email']])
    return render_template('my_primers.html', primers=primers)

# wyświetlanie danego primera
@app.route('/primer/<int:x>')
def show_primer(x):
    primers = query_db('select * from primers where pid=?', [x,])
    if not primers:
        abort(404)
    return render_template('show_primer.html', primers=primers)

# dodawanie nowego primera
@app.route('/add_primer', methods=['GET', 'POST'])
def add_primer():
    if 'email' not in session:
        abort(401)
    if request.method == 'POST':
        db = get_db()
        db.execute('insert into primers (pname, ptype, psequence, nt, temp_gen, temp_calc, oligo_date, buffer, prep_date, gene_name, gb_acc_no, ncbi_id, ncbi_pa, gene_comment, genus, species, gene_desc, plasmid_name, seq_desc, seq_list, matrix_prep, cycles, final_conc, info, pmid, order_date, firm, facture_no, keywords, status, owner) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    [request.form['pname'], request.form['ptype'], request.form['psequence'].upper(), request.form['nt'], request.form['temp_gen'], request.form['temp_calc'], request.form['oligo_date'], request.form['buffer'], request.form['prep_date'], request.form['gene_name'], request.form['gb_acc_no'], request.form['ncbi_id'], request.form['ncbi_pa'], request.form['gene_comment'], request.form['genus'], request.form['species'], request.form['gene_desc'], request.form['plasmid_name'], request.form['seq_desc'], request.form['seq_list'], request.form['matrix_prep'], request.form['cycles'], request.form['final_conc'], request.form['info'], request.form['pmid'], request.form['order_date'], request.form['firm'], request.form['facture_no'], request.form['keywords'], request.form['status'], session['email']])
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
    primer = query_db('select * from primers where pid=?', [x,], one=True)
    if primer is None:
        abort(404)
    elif session['email'] != primer['owner']:
        abort(401)
    # właściwa funkcja
    primers = query_db('select * from primers where pid=? and owner=?', [x, session['email']])
    if request.method == 'POST':
        db = get_db()
        db.execute('update primers set pname=?, ptype=?, psequence=?, nt=?, temp_gen=?, temp_calc=?, oligo_date=?, buffer=?, prep_date=?, gene_name=?, gb_acc_no=?, ncbi_id=?, ncbi_pa=?, gene_comment=?, genus=?, species=?, gene_desc=?, plasmid_name=?, seq_desc=?, seq_list=?, matrix_prep=?, cycles=?, final_conc=?, info=?, pmid=?, order_date=?, firm=?, facture_no=?, keywords=?, status=? where pid=?',
					[request.form['pname'], request.form['ptype'], request.form['psequence'], request.form['nt'], request.form['temp_gen'], request.form['temp_calc'], request.form['oligo_date'], request.form['buffer'], request.form['prep_date'], request.form['gene_name'], request.form['gb_acc_no'], request.form['ncbi_id'], request.form['ncbi_pa'], request.form['gene_comment'], request.form['genus'], request.form['species'], request.form['gene_desc'], request.form['plasmid_name'], request.form['seq_desc'], request.form['seq_list'], request.form['matrix_prep'], request.form['cycles'], request.form['final_conc'], request.form['info'], request.form['pmid'], request.form['order_date'], request.form['firm'], request.form['facture_no'], request.form['keywords'], request.form['status'], x])
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

# pobieranie pdf
@app.route('/get_pdf/', methods=['GET', 'POST'])

def pdf_template():
    #query_db('select * from primers where pid=?', [x,])
    with app.app_context():
        pdf = pdfkit.from_url('http://localhost:5000/primer/1', False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Connect-Disposition'] = 'attachment; filename = output.pdf'

        return response

# obsługa błędu odpowiedzi 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('error404.html'), 404

# obsługa błędu autoryzacji 401
@app.errorhandler(401)
def page_unauthorized(error):
    return render_template('error401.html'), 401

if __name__ == '__main__':
    app.run()

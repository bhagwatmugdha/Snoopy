from app import app, mysql
from flask import render_template, flash, request, redirect, url_for, session, logging
from passlib.hash import sha256_crypt
from functools import wraps
#from models import Member
from forms import RegisterForm, ArticleForm
import os
from werkzeug.utils import secure_filename

 # @app.route('/')
# def index():
# 	firstmember = Member.query.first()
# 	return '<h1>The first member is:'+ firstmember.name +'</h1>'
 # Index
@app.route('/')
def index():
	return  render_template('home.html')
 # About
@app.route('/about')
def about():
	return  render_template('about.html')
 # Articles
@app.route('/articles')
def articles():
		# Create cursor
	cur = mysql.connection.cursor()
 	# Get articles
	result = cur.execute("SELECT * FROM articles")
 	articles = cur.fetchall()
 	if result > 0:
		return render_template('articles.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('articles.html', msg=msg)
	# Close connection
	cur.close()
 # Single Article
@app.route('/article/<string:id>/')
def article(id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Get article
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
 	article = cur.fetchone()
 	return  render_template('article.html', article=article)
 # Register
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute query
		cur.execute("INSERT INTO users(name , email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('You are now registered and can log in', 'success')
 		return redirect(url_for('login'))
	return render_template('register.html', form=form)
 # Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields (not using WTForms)
		username = request.form['username']
		password_candidate = request.form['password']
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
 		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']
 			# Compare passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username
 				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invlaid login'
				return render_template('login.html', error=error)
			# Close connection
			cur.close()
 		else:
			error = 'Username not found'
			return render_template('login.html', error=error)
 	return render_template('login.html')

# Apply
ALLOWED_EXTENSIONS = set(['pdf'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/apply', methods=['GET', 'POST'])
def apply():
	if request.method == 'POST':
		# Get Form Fields (not using WTForms)
		# resume = request.form['resume']
		github_username = request.form['github_username']
		if github_username == '':
			flash('Please enter your github username', 'danger')
			return render_template('apply.html')
		if 'file' not in request.files:
			flash('Please upload your resume', 'danger')
			return render_template('apply.html')
		file = request.files['file']
		if file.filename == '':
			flash('Please upload your resume', 'danger')
			return render_template('apply.html')
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			# insert into db
			flash('Successfully Uploaded '+str(github_username), 'success')
		else:
			flash('Please upload a valid format', 'danger')
 	return render_template('apply.html')



 # Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap
 # Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))
 # Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	# Create cursor
	cur = mysql.connection.cursor()
 	# Get articles
	result = cur.execute("SELECT * FROM articles WHERE author=%s", (session['username'],))
 	articles = cur.fetchall()
 	if result > 0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('dashboard.html', msg=msg)
	# Close connection
	cur.close()

 # Analyze
@app.route('/analyze', methods=['GET', 'POST'])
@is_logged_in
def analyze():
	if request.method == 'POST':
		nop = request.form['nop']
		skilla, skillb, skillc, skilld = 0, 0, 0, 0
		if request.form.get('skilla'):
			skilla = 1
		if request.form.get('skillb'):
			skillb = 1
		if request.form.get('skillc'):
			skillc = 1
		if request.form.get('skilld'):
			skilld = 1

		# session['nop'] = nop
		session['nop'], session['skilla'], session['skillb'], session['skillc'], session['skilld'] = nop, skilla, skillb, skillc, skilld

		# flash(str(nop)+" "+str(skilla)+" "+str(skillb)+" "+str(skillc)+" "+str(skilld), 'success')
		return redirect(url_for('results'))
	# # Create cursor
	# cur = mysql.connection.cursor()
 	# # Get articles
	# result = cur.execute("SELECT * FROM articles WHERE author=%s", (session['username'],))
 	# articles = cur.fetchall()
 	# if result > 0:
	# 	return render_template('analyze.html', articles=articles)
	# else:
	# 	msg = 'No Articles Found'
	# 	return render_template('analyze.html', msg=msg)
	# # Close connection
	# cur.close()
	
	return render_template('analyze.html')

 # Results
@app.route('/results')
@is_logged_in
def results():

	nop, skilla, skillb, skillc, skilld = session.get('nop'), session.get('skilla'), session.get('skillb'), session.get('skillc'), session.get('skilld', None)
	flash(str(nop)+" "+str(skilla)+" "+str(skillb)+" "+str(skillc)+" "+str(skilld), 'success')
	# flash('str(nop)', 'success')

	# Create cursor
	cur = mysql.connection.cursor()
 	# Get articles
	result = cur.execute("SELECT * FROM articles WHERE author=%s", (session['username'],))
 	articles = cur.fetchall()
 	if result > 0:
		return render_template('results.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('results.html', msg=msg)
	# Close connection
	cur.close()

 # Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute
		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('Article Created', 'success')
 		return redirect(url_for('dashboard'))
 	return render_template('add_article.html', form=form)
 # Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Get article by id
	result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])
 	article = cur.fetchone()
 	# Get form
	form = ArticleForm(request.form)
 	# Populate article form fields
	form.title.data = article['title']
	form.body.data = article['body']
 	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
 		# Create cursor
		cur = mysql.connection.cursor()
 		# Execute
		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
 		# Commit to DB
		mysql.connection.commit()
 		# Close connection
		cur.close()
 		flash('Article Updated', 'success')
 		return redirect(url_for('dashboard'))
 	return render_template('edit_article.html', form=form)
 # Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	# Create cursor
	cur = mysql.connection.cursor()
 	# Execute
	cur.execute("DELETE FROM articles WHERE id=%s", [id])
 	# Commit to DB
	mysql.connection.commit()
 	# Close connection
	cur.close()
 	flash('Article Deleted', 'success')
 	return redirect(url_for('dashboard'))
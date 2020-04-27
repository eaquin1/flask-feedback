from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import RegisterForm, LoginForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///flask-feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route("/")
def redirect_register():
    """Home route redirects to register"""
    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Render and handle form to register/create a user"""
    form = RegisterForm()
    if form.validate_on_submit():
        data = {k: v for k, v in form.data.items() if k != "csrf_token"}
        
        new_user = User.register(**data)
        
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        flash('Welcome! Succesfully created your account!')
        return redirect(f'/users/{new_user.username}')
    return render_template("register.html", form=form)

@app.route("/users/<username>")
def users(username):
    """Render users page"""
    user = User.query.filter_by(username=username).first()
    return render_template("user.html", user=user)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Render and handle form to login a user"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        auth_user = User.authenticate(username, password)

        if auth_user:
            flash(f"Welcome back, {auth_user.username}")
            session['username'] = auth_user.username
            return redirect(f'/users/{auth_user.username}')
        else:
            form.username.errors = ['Invalid username/password']

    return render_template("login.html", form=form)

@app.route("/logout")
def logout_user():
    """Logout User"""
    session.pop('username')
    flash('Goodbye!')
    return redirect('/login')
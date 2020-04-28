from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from werkzeug.exceptions import Unauthorized

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
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()

    if form.validate_on_submit():
        data = {k: v for k, v in form.data.items() if k != "csrf_token"}
        
        new_user = User.register(**data)
        
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        flash('Welcome! Successfully created your account!')
        return redirect(f'/users/{session["username"]}')
    else:
        return render_template("users/register.html", form=form)

@app.route("/users/<username>")
def users(username):
    """Render users page"""
    
    if 'username' not in session or username != session['username']:
        raise Unauthorized()
    else:
        user = User.query.get(username)
        return render_template("users/user.html", user=user)
        

@app.route("/login", methods=["GET", "POST"])
def login():
    """Render and handle form to login a user"""
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        auth_user = User.authenticate(username, password) # <User> or False

        if auth_user:
            flash(f"Welcome back, {auth_user.username}")
            session['username'] = auth_user.username
            return redirect(f'/users/{auth_user.username}')
        else:
            form.username.errors = ['Invalid username/password']
            return render_template("users/login.html", form=form)
    return render_template("users/login.html", form=form)

@app.route("/logout")
def logout_user():
    """Logout User"""
    session.pop('username')
    flash('Goodbye!')
    return redirect('/login')

@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """Delete user and associated feedback"""
    if 'username' not in session or username != session['username']:
        raise Unauthorized()
    else:
        user = User.query.filter_by(username=username).first()
        db.session.delete(user)
        db.session.commit()
        session.pop('username')
        flash(f"User {username} deleted")
        return redirect("/register")

@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    """Render and handle form to add feedback"""
    user = User.query.get(username)
    if 'username' not in session or username != session['username']:
        raise Unauthorized()
    else:
        form = FeedbackForm()
        if form.validate_on_submit():
            
            title = form.title.data
            content = form.content.data
            username = user.username
            feedback = Feedback(title=title, content=content, username=username)
            db.session.add(feedback)
            db.session.commit()
            return redirect(f"/users/{username}")
        return render_template("feedback/new.html", form=form, user=user)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def edit_feedback(feedback_id):
    """Render and handle form to add feedback"""
    feedback = Feedback.query.get(feedback_id)

    if 'username' not in session or feedback.username != session['username']:
        raise Unauthorized()
    
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        return redirect(f"/users/{feedback.username}")

    return render_template("feedback/edit.html", form=form, feedback=feedback)

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    db.session.delete(feedback)
    db.session.commit()
    flash("Feedback deleted")
    return redirect(f'/users/{feedback.username}')



from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Subject, RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'arya_partner_key_99'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data, gmail=form.gmail.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(gmail=form.gmail.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name, subjects=current_user.subjects)

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    sub_name = request.form.get('sub_name')
    if sub_name:
        new_sub = Subject(name=sub_name, user_id=current_user.id)
        db.session.add(new_sub)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/mark/<int:sub_id>/<string:status>', methods=['POST'])
@login_required
def mark(sub_id, status):
    sub = Subject.query.get(sub_id)
    if sub and sub.user_id == current_user.id:
        sub.total_classes += 1
        if status == 'present':
            sub.present_count += 1
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
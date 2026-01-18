from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Subject, AttendanceRecord, RegistrationForm, LoginForm
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'arya_logic_secure_77'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/', methods=['GET', 'POST'])
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
    today = date.today()
    # Find all subject IDs the user already marked TODAY
    records_today = AttendanceRecord.query.filter(
        AttendanceRecord.date_marked == today
    ).all()
    marked_ids = [r.subject_id for r in records_today]
    
    return render_template('dashboard.html', 
                           name=current_user.name, 
                           subjects=current_user.subjects, 
                           marked_ids=marked_ids)
@app.route('/mark/<int:sub_id>/<string:status>/<string:session_type>', methods=['POST'])
@login_required
def mark(sub_id, status, session_type):
    today = date.today()
    
    # Check if this subject was already marked TODAY
    existing = AttendanceRecord.query.filter_by(subject_id=sub_id, date_marked=today).first()
    
    if not existing:
        sub = Subject.query.get(sub_id)
        
        # Determine the "weight" of the class
        if session_type == 'lab':
            weight = 2
        elif session_type == 'extra':
            weight = 1  # You can change this to 0 if extra classes shouldn't affect %
        else: # Normal Class
            weight = 1
            
        # Update the counts based on weight
        sub.total_classes += weight
        if status == 'present':
            sub.present_count += weight
        
        # Save the record
        new_record = AttendanceRecord(subject_id=sub_id, status=status)
        db.session.add(new_record)
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    sub_name = request.form.get('sub_name')
    if sub_name:
        new_sub = Subject(name=sub_name, user_id=current_user.id)
        db.session.add(new_sub)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_subject/<int:sub_id>', methods=['POST'])
@login_required
def delete_subject(sub_id):
    # Find the subject
    subject_to_delete = Subject.query.get(sub_id)
    
    # Security Check: Ensure the subject belongs to the current user
    if subject_to_delete and subject_to_delete.user_id == current_user.id:
        # First, delete all attendance records associated with this subject
        AttendanceRecord.query.filter_by(subject_id=sub_id).delete()
        
        # Then, delete the subject itself
        db.session.delete(subject_to_delete)
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
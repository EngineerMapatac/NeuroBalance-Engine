import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from engine import NeuroBalanceEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'neurobalance-secret-key')

# Database Config
db_url = os.getenv('DATABASE_URL', 'sqlite:///users.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

# Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

db = SQLAlchemy(app)
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    loans = db.relationship('Loan', backref='user', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    principal = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    months = db.Column(db.Integer, nullable=False)
    extra = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), nullable=False)
    total_interest = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def home():
    results = None
    inputs = {'currency': '₱'}

    if request.method == 'POST':
        try:
            principal = float(request.form['principal'])
            months = int(request.form['months'])
            extra_raw = request.form.get('extra')
            extra = float(extra_raw) if extra_raw else 0.00
            currency = request.form.get('currency', '₱')
            total_payable_raw = request.form.get('total_payable')
            rate_raw = request.form.get('rate')

            if total_payable_raw:
                total_payable = float(total_payable_raw)
                monthly_pmt = total_payable / months
                engine = NeuroBalanceEngine(principal, months, monthly_payment=monthly_pmt)
                rate = round((engine.monthly_rate * 100), 2)
            else:
                rate = float(rate_raw)
                engine = NeuroBalanceEngine(principal, months, monthly_interest_rate=rate)
                total_payable = ""

            df = engine.generate_schedule(extra_payment=extra)
            total_interest = df["Interest"].sum()
            months_saved = months - len(df)
            schedule_data = df.to_dict(orient='records')

            results = {
                "total_interest": f"{currency}{total_interest:,.2f}",
                "months_saved": months_saved,
                "actual_months": len(df),
                "schedule": schedule_data,
                "currency": currency
            }
            inputs = {
                "principal": principal, "rate": rate, "months": months, 
                "extra": extra, "currency": currency, "total_payable": total_payable
            }
        except ValueError:
            results = {"error": "Invalid input. Please enter numbers only."}

    return render_template('index.html', results=results, inputs=inputs, user=current_user)

@app.route('/export', methods=['POST'])
def export():
    principal = float(request.form['principal'])
    months = int(request.form['months'])
    extra_raw = request.form.get('extra')
    extra = float(extra_raw) if extra_raw else 0.00
    rate_raw = request.form.get('rate')
    total_payable_raw = request.form.get('total_payable')

    if total_payable_raw:
        total_payable = float(total_payable_raw)
        monthly_pmt = total_payable / months
        engine = NeuroBalanceEngine(principal, months, monthly_payment=monthly_pmt)
    else:
        rate = float(rate_raw)
        engine = NeuroBalanceEngine(principal, months, monthly_interest_rate=rate)

    df = engine.generate_schedule(extra_payment=extra)
    output = df.to_csv(index=False)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=neurobalance_schedule.csv"}
    )

@app.route('/save_loan', methods=['POST'])
@login_required
def save_loan():
    new_loan = Loan(
        user_id=current_user.id,
        principal=float(request.form['principal']),
        rate=float(request.form['rate']),
        months=int(request.form['months']),
        extra=float(request.form['extra']),
        currency=request.form['currency'],
        total_interest=request.form['total_interest']
    )
    db.session.add(new_loan)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_loans = Loan.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', loans=user_loans, user=current_user)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access Denied. Admins only.", 403
    all_users = User.query.all()
    all_loans = Loan.query.all()
    return render_template('admin.html', users=all_users, loans=all_loans)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email address already exists.')
            return redirect(url_for('signup'))
            
        is_admin = True if email == 'admin@neurobalance.com' else False
        
        # Admins are auto-verified, regular users are not
        is_verified = True if is_admin else False
        
        new_user = User(name=name, email=email, password=generate_password_hash(password, method='pbkdf2:sha256'), is_admin=is_admin, is_verified=is_verified)
        db.session.add(new_user)
        db.session.commit()

        if not is_admin:
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            msg = Message('Verify your NeuroBalance Account', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
            msg.body = f'Welcome to NeuroBalance! Click here to verify your account: {link}'
            try:
                mail.send(msg)
                flash('An email has been sent to you. Please verify your account.')
            except Exception:
                flash('Account created, but email failed to send. Please contact admin.')
            return redirect(url_for('login'))
        else:
            flash('Admin account created and verified.')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already verified. Please log in.')
    else:
        user.is_verified = True
        db.session.commit()
        flash('You have verified your account. Thanks!')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
            
        if not user.is_verified:
            flash('Please verify your email address before logging in.')
            return redirect(url_for('login'))
            
        login_user(user)
        
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
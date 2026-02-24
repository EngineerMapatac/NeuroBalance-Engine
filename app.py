from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from engine import NeuroBalanceEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neurobalance-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('signup'))

        new_user = User(name=name, email=email, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
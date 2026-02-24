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

            df = engine.generate_schedule(extra_payment=extra)
            total_interest = df["Interest"].sum()
            months_saved = months - len(df)
            schedule_data = df.to_dict(orient='records')

            results = {
                "total_interest": f"{currency}{total_interest:,.2f}",
                "months_
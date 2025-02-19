from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, Stock, Transaction
from stock_price_generator import update_stock_prices
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, StockForm, MarketHoursForm, MarketScheduleForm, AddCashForm, WithdrawCashForm

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(user=user)
    return dict(user=None)

@app.route('/')
def index():
    stocks = Stock.query.all()
    return render_template('index.html', stocks=stocks)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        full_name = form.full_name.data
        username = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        user = User(full_name=full_name, username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    add_cash_form = AddCashForm()
    withdraw_cash_form = WithdrawCashForm()
    return render_template('portfolio.html', user=user, add_cash_form=add_cash_form, withdraw_cash_form=withdraw_cash_form)

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin.html')

@app.route('/create_stock', methods=['GET', 'POST'])
def create_stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    form = StockForm()
    if form.validate_on_submit():
        company_name = form.company_name.data
        ticker = form.ticker.data
        volume = form.volume.data
        initial_price = form.initial_price.data
        stock = Stock(company_name=company_name, ticker=ticker, volume=volume, initial_price=initial_price, current_price=initial_price)
        db.session.add(stock)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('create_stock.html', form=form)

@app.route('/market_hours', methods=['GET', 'POST'])
def market_hours():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    form = MarketHoursForm()
    if form.validate_on_submit():
        # ...handle market hours update...
        pass
    return render_template('market_hours.html', form=form)

@app.route('/market_schedule', methods=['GET', 'POST'])
def market_schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    form = MarketScheduleForm()
    if form.validate_on_submit():
        # ...handle market schedule update...
        pass
    return render_template('market_schedule.html', form=form)

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stock_id = request.form['stock_id']
    amount = int(request.form['amount'])
    stock = Stock.query.get(stock_id)
    total_price = stock.current_price * amount
    if user.cash_account >= total_price:
        user.cash_account -= total_price
        transaction = Transaction(user_id=user.id, stock_id=stock.id, transaction_type='buy', amount=amount, price=stock.current_price)
        db.session.add(transaction)
        db.session.commit()
    return redirect(url_for('portfolio'))

@app.route('/sell_stock', methods=['POST'])
def sell_stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stock_id = request.form['stock_id']
    amount = int(request.form['amount'])
    stock = Stock.query.get(stock_id)
    total_price = stock.current_price * amount
    transaction = Transaction(user_id=user.id, stock_id=stock.id, transaction_type='sell', amount=amount, price=stock.current_price)
    user.cash_account += total_price
    db.session.add(transaction)
    db.session.commit()
    return redirect(url_for('portfolio'))

@app.route('/add_cash', methods=['POST'])
def add_cash():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    form = AddCashForm()
    if form.validate_on_submit():
        amount = form.amount.data
        user.cash_account += amount
        db.session.commit()
    return redirect(url_for('portfolio'))

@app.route('/withdraw_cash', methods=['POST'])
def withdraw_cash():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    form = WithdrawCashForm()
    if form.validate_on_submit():
        amount = form.amount.data
        if user.cash_account >= amount:
            user.cash_account -= amount
            db.session.commit()
    return redirect(url_for('portfolio'))

if __name__ == '__main__':
    app.run(debug=True)

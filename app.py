from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, Stock, StockHistory, Transaction, Order, MarketHours, MarketSchedule
from forms import RegistrationForm, LoginForm, StockForm, MarketHoursForm, MarketScheduleForm, AddCashForm, WithdrawCashForm, UpdateProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_pending_orders_job():
    pending_orders = Order.query.filter_by(status='pending').all()
    for order in pending_orders:
        if order.order_type == 'buy':
            transaction = Transaction(user_id=order.user_id, stock_id=order.stock_id, amount=order.amount, price=order.price, transaction_type='buy')
            db.session.add(transaction)
            user = User.query.get(order.user_id)
            user.cash_account -= order.amount * order.price
        elif order.order_type == 'sell':
            transaction = Transaction(user_id=order.user_id, stock_id=order.stock_id, amount=order.amount, price=order.price, transaction_type='sell')
            db.session.add(transaction)
            user = User.query.get(order.user_id)
            user.cash_account += order.amount * order.price
        order.status = 'completed'
    try:
        db.session.commit()
        logger.info("Pending orders processed automatically.")
    except Exception as e:
        logger.error(f"Automatic processing of pending orders failed: {e}")
        db.session.rollback()

# Add the job to the scheduler
def start_scheduler():
    from stock_price_generator import update_stock_prices  # Import within the function to avoid circular import
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_stock_prices, 'interval', minutes=1)  # Update stock prices every minute
    scheduler.start()
    logger.info("Scheduler started and job added to update stock prices every minute.")

# Start the scheduler
start_scheduler()

@app.template_filter('to_float')
def to_float(value):
    return float(value)

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
    
    # Calculate the net amount of each stock the user owns
    stocks_owned = db.session.query(
        Stock.id, Stock.company_name, Stock.ticker, Stock.current_price,
        db.func.sum(Transaction.amount).label('total_amount')
    ).join(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'buy'
    ).group_by(Stock.id).all()
    
    stocks_sold = db.session.query(
        Stock.id, db.func.sum(Transaction.amount).label('total_amount')
    ).join(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == 'sell'
    ).group_by(Stock.id).all()
    
    stocks_owned_dict = {stock.id: {'company_name': stock.company_name, 'ticker': stock.ticker, 'current_price': stock.current_price, 'total_amount': stock.total_amount} for stock in stocks_owned}
    for stock in stocks_sold:
        if stock.id in stocks_owned_dict:
            stocks_owned_dict[stock.id]['total_amount'] -= stock.total_amount
    
    stocks_owned = [stock for stock in stocks_owned_dict.values() if stock['total_amount'] > 0]
    
    return render_template('portfolio.html', user=user, add_cash_form=add_cash_form, withdraw_cash_form=withdraw_cash_form, stocks_owned=stocks_owned)

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        flash('You do not have permission to cancel this order.', 'danger')
        return redirect(url_for('orders'))
    if order.status == 'pending':
        order.status = 'cancelled'
        db.session.commit()
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Order cannot be cancelled.', 'danger')
    return redirect(url_for('orders'))

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
        day_of_week = form.day_of_week.data
        open_time = form.open_time.data
        close_time = form.close_time.data
        market_hours = MarketHours.query.filter_by(day_of_week=day_of_week).first()
        if market_hours:
            market_hours.open_time = open_time
            market_hours.close_time = close_time
        else:
            market_hours = MarketHours(day_of_week=day_of_week, open_time=open_time, close_time=close_time)
            db.session.add(market_hours)
        db.session.commit()
        return redirect(url_for('market_hours'))
    market_hours = MarketHours.query.all()
    return render_template('market_hours.html', form=form, market_hours=market_hours)

@app.route('/market_schedule', methods=['GET', 'POST'])
def market_schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    form = MarketScheduleForm()
    if form.validate_on_submit():
        date = form.date.data
        description = form.description.data
        is_closed = form.is_closed.data
        market_schedule = MarketSchedule.query.filter_by(date=date).first()
        if market_schedule:
            market_schedule.description = description
            market_schedule.is_closed = is_closed
        else:
            market_schedule = MarketSchedule(date=date, description=description, is_closed=is_closed)
            db.session.add(market_schedule)
        db.session.commit()
        return redirect(url_for('market_schedule'))
    market_schedule = MarketSchedule.query.all()
    return render_template('market_schedule.html', form=form, market_schedule=market_schedule)

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
        order = Order(user_id=user.id, stock_id=stock.id, order_type='buy', amount=amount, price=stock.current_price, status='pending')
        db.session.add(order)
        db.session.commit()
        flash('Order placed successfully.', 'success')
    else:
        flash('You do not have enough money to place this order.', 'danger')
    return redirect(url_for('portfolio'))

@app.route('/sell_stock', methods=['POST'])
def sell_stock():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    stock_id = request.form['stock_id']
    amount = int(request.form['amount'])
    stock = Stock.query.get(stock_id)
    
    # Calculate the total amount of stock the user owns
    total_owned = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=user.id, stock_id=stock_id, transaction_type='buy').scalar() or 0
    total_sold = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=user.id, stock_id=stock_id, transaction_type='sell').scalar() or 0
    net_owned = total_owned - total_sold
    
    if amount > net_owned:
        flash('You do not have enough stock to sell.', 'danger')
    else:
        total_price = stock.current_price * amount
        order = Order(user_id=user.id, stock_id=stock.id, order_type='sell', amount=amount, price=stock.current_price, status='pending')
        db.session.add(order)
        db.session.commit()
        flash('Order placed successfully.', 'success')
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    form = UpdateProfileForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        return redirect(url_for('profile'))
    form.email.data = user.email
    return render_template('profile.html', form=form)

@app.route('/stock_history/<int:stock_id>')
def stock_history(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    history = StockHistory.query.filter_by(stock_id=stock.id).order_by(StockHistory.timestamp.desc()).all()
    return render_template('stock_history.html', stock=stock, history=history)

@app.route('/view_stock/<int:stock_id>')
def view_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    return render_template(
        'view_stock.html',
        stock=stock,
        high_price=stock.high_price,
        low_price=stock.low_price
    )

@app.route('/update_stock_price', methods=['GET', 'POST'])
def update_stock_price():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        stock_id = request.form['stock_id']
        new_price = float(request.form['new_price'])
        stock = Stock.query.get(stock_id)
        if stock:
            stock.current_price = new_price
            db.session.commit()
            flash('Stock price updated successfully.', 'success')
        else:
            flash('Stock not found.', 'danger')
        return redirect(url_for('update_stock_price'))
    stocks = Stock.query.all()
    return render_template('update_stock_price.html', stocks=stocks)

@app.route('/edit_stock_price/<int:stock_id>', methods=['POST'])
def edit_stock_price(stock_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    stock = Stock.query.get_or_404(stock_id)
    new_price = float(request.form['new_price'])
    stock.current_price = new_price
    # Log the price change in StockHistory
    stock_history = StockHistory(stock_id=stock.id, price=new_price)
    db.session.add(stock_history)
    db.session.commit()
    flash('Stock price updated successfully.', 'success')
    return redirect(url_for('view_stock', stock_id=stock.id))

@app.route('/process_pending_orders', methods=['POST'])
def process_pending_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return redirect(url_for('index'))
    pending_orders = Order.query.filter_by(status='pending').all()
    for order in pending_orders:
        if order.order_type == 'buy':
            transaction = Transaction(user_id=order.user_id, stock_id=order.stock_id, amount=order.amount, price=order.price, transaction_type='buy')
            db.session.add(transaction)
            user = User.query.get(order.user_id)
            user.cash_account -= order.amount * order.price
        elif order.order_type == 'sell':
            transaction = Transaction(user_id=order.user_id, stock_id=order.stock_id, amount=order.amount, price=order.price, transaction_type='sell')
            db.session.add(transaction)
            user = User.query.get(order.user_id)
            user.cash_account += order.amount * order.price
        order.status = 'completed'
    try:
        db.session.commit()
        logger.info("Manual processing of pending orders successful.")
    except Exception as e:
        logger.error(f"Manual processing of pending orders failed: {e}")
        db.session.rollback()
    flash('Pending orders processed successfully.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=False)

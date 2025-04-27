from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    cash_account = db.Column(db.Float, default=0.0)
    is_admin = db.Column(db.Boolean, default=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), nullable=False, unique=True)
    volume = db.Column(db.Integer, nullable=False)
    initial_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=True)  # New field
    low_price = db.Column(db.Float, nullable=True)   # New field
    transactions = db.relationship('Transaction', backref='stock', lazy=True)
    orders = db.relationship('Order', backref='stock', lazy=True)

class StockHistory(db.Model):
    __tablename__ = 'stock_price_history'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    transaction_type = db.Column(db.String(10))
    amount = db.Column(db.Integer)
    price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    order_type = db.Column(db.String(10))
    amount = db.Column(db.Integer)
    price = db.Column(db.Float)
    status = db.Column(db.String(10), default='pending')
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class MarketHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10))
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)

class MarketSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True)
    description = db.Column(db.String(200))
    is_closed = db.Column(db.Boolean, default=False)

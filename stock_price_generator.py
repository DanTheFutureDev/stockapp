import random
from models import db, Stock

def update_stock_prices():
    stocks = Stock.query.all()
    for stock in stocks:
        change = random.uniform(-0.05, 0.05)  # Random change between -5% and +5%
        stock.current_price += stock.current_price * change
        db.session.commit()

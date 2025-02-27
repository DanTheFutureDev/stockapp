import random
from datetime import datetime
from models import db, Stock, StockHistory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Add an explicit StreamHandler to ensure console output
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def generate_random_price(current_price):
    change_percent = random.uniform(-0.05, 0.05)  # Random change between -5% and 5%
    new_price = current_price * (1 + change_percent)
    return round(new_price, 2)

def update_stock_prices():
    logger.info("Updating stock prices...")
    from app import app  # Import app within the function to avoid circular import
    with app.app_context():
        stocks = Stock.query.all()
        for stock in stocks:
            new_price = generate_random_price(stock.current_price)
            logger.info(f"Updating {stock.ticker} from {stock.current_price} to {new_price}")
            stock.current_price = new_price
            stock_history = StockHistory(stock_id=stock.id, price=new_price)
            db.session.add(stock_history)
        db.session.commit()
        logger.info(f"Stock prices updated at {datetime.now()}")
    logger.info("Stock prices updated.")

if __name__ == '__main__':
    update_stock_prices()

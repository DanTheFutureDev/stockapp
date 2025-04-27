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
        current_date = datetime.now().date()
        
        for stock in stocks:
            new_price = generate_random_price(stock.current_price)

            # Set opening price if it's a new day
            if not stock.opening_price or not stock.last_updated or stock.last_updated.date() != current_date:

                stock.opening_price = new_price
                stock.high_price = new_price
                stock.low_price = new_price
            else:
                if new_price > (stock.high_price or 0):
                    stock.high_price = new_price
                if new_price < (stock.low_price or new_price):
                    stock.low_price = new_price

            logger.info(f"Updating {stock.ticker} from {stock.current_price} to {new_price}")
            stock.current_price = new_price
            stock.last_updated = datetime.now()  # You can add this column to track update time

            stock_history = StockHistory(stock_id=stock.id, price=new_price)
            db.session.add(stock_history)

        db.session.commit()
        logger.info(f"Stock prices updated at {datetime.now()}")

if __name__ == '__main__':
    update_stock_prices()

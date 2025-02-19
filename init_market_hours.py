from app import app
from models import db, MarketHours
from datetime import time

with app.app_context():
    market_hours = [
        {'day_of_week': 'Monday', 'open_time': time(9, 30), 'close_time': time(16, 0)},
        {'day_of_week': 'Tuesday', 'open_time': time(9, 30), 'close_time': time(16, 0)},
        {'day_of_week': 'Wednesday', 'open_time': time(9, 30), 'close_time': time(16, 0)},
        {'day_of_week': 'Thursday', 'open_time': time(9, 30), 'close_time': time(16, 0)},
        {'day_of_week': 'Friday', 'open_time': time(9, 30), 'close_time': time(16, 0)},
    ]
    for mh in market_hours:
        market_hour = MarketHours.query.filter_by(day_of_week=mh['day_of_week']).first()
        if not market_hour:
            market_hour = MarketHours(day_of_week=mh['day_of_week'], open_time=mh['open_time'], close_time=mh['close_time'])
            db.session.add(market_hour)
    db.session.commit()
    print("Market hours initialized!")

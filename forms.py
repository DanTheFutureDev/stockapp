from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StockForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    ticker = StringField('Ticker', validators=[DataRequired()])
    volume = IntegerField('Volume', validators=[DataRequired()])
    initial_price = FloatField('Initial Price', validators=[DataRequired()])
    submit = SubmitField('Create Stock')

class MarketHoursForm(FlaskForm):
    day_of_week = StringField('Day of Week', validators=[DataRequired()])
    open_time = StringField('Open Time', validators=[DataRequired()])
    close_time = StringField('Close Time', validators=[DataRequired()])
    submit = SubmitField('Update')

class MarketScheduleForm(FlaskForm):
    # Add fields for market schedule
    submit = SubmitField('Update')

class AddCashForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Add Cash')

class WithdrawCashForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Withdraw Cash')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password', message="Passwords must match")])
    submit = SubmitField("Create Account")

class LoginForm(FlaskForm):
    identifier = StringField("Username or Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")

class AddBookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    author = StringField("Author", validators=[DataRequired(), Length(max=150)])
    isbn = StringField("ISBN", validators=[DataRequired(), Length(max=20)])
    genre = StringField("Genre", validators=[Optional(), Length(max=80)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Add Book")

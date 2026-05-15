from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # simple relationship; for beginners this behaves like a Python list
    borrowings = db.relationship("Borrowing", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    genre = db.Column(db.String(80))
    description = db.Column(db.Text)
    availability_status = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrowings = db.relationship("Borrowing", backref="book", lazy=True)

    @property
    def is_available(self):
        return self.availability_status

    def __repr__(self):
        return f"<Book {self.title}>"


class Borrowing(db.Model):
    __tablename__ = "borrowings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="borrowed")

    @property
    def is_overdue(self):
        if self.status == "borrowed" and self.due_date:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self):
        return f"<Borrowing user={self.user_id} book={self.book_id} status={self.status}>"

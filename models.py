from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")  # 'admin' | 'member'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrowings = db.relationship("Borrowing", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def active_borrowings_count(self):
        return self.borrowings.filter_by(status="borrowed").count()

    def __repr__(self):
        return f"<User {self.username}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    genre = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)
    availability_status = db.Column(db.Boolean, default=True, nullable=False)  # True = available
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrowings = db.relationship("Borrowing", backref="book", lazy="dynamic")

    @property
    def is_available(self):
        return self.availability_status

    @property
    def borrow_count(self):
        return self.borrowings.count()

    def __repr__(self):
        return f"<Book {self.title}>"


class Borrowing(db.Model):
    __tablename__ = "borrowings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="borrowed", nullable=False)  # 'borrowed' | 'returned' | 'overdue'

    @property
    def is_overdue(self):
        if self.status == "borrowed" and self.due_date:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self):
        return f"<Borrowing user={self.user_id} book={self.book_id} status={self.status}>"

import os
from flask import Flask
from models import db, User, Book
from config import config
from routes import main


def create_app(config_name=None):
    # simple factory: use provided config or default
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # initialize database and register routes
    db.init_app(app)
    app.register_blueprint(main)

    # Create tables and seed a couple of records for a fresh DB
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    # Seed only if the DB is empty
    if User.query.first():
        return

    admin = User(username="admin", email="admin@library.dev", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)

    demo = User(username="alice", email="alice@library.dev", role="member")
    demo.set_password("alice123")
    db.session.add(demo)

    sample_books = [
        Book(title="Clean Code", author="Robert C. Martin", isbn="978-0132350884"),
        Book(title="1984", author="George Orwell", isbn="978-0451524935"),
    ]

    for b in sample_books:
        db.session.add(b)

    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

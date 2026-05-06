import os
from flask import Flask
from models import db, User, Book, Borrowing
from config import config
from routes import main


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main)

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Seed initial admin user and sample books if DB is empty."""
    if User.query.first():
        return

    admin = User(username="admin", email="admin@library.dev", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)

    demo = User(username="alice", email="alice@library.dev", role="member")
    demo.set_password("alice123")
    db.session.add(demo)

    sample_books = [
        Book(title="The Pragmatic Programmer", author="Andrew Hunt & David Thomas",
                isbn="978-0135957059", genre="Technology",
                description="A classic guide to software craftsmanship."),
        Book(title="Clean Code", author="Robert C. Martin",
                isbn="978-0132350884", genre="Technology",
                description="A handbook of agile software craftsmanship."),
        Book(title="Dune", author="Frank Herbert",
                isbn="978-0441013593", genre="Science Fiction",
                description="A sweeping tale of a desert planet and its people."),
        Book(title="1984", author="George Orwell",
                isbn="978-0451524935", genre="Fiction",
                description="A dystopian social science fiction novel."),
        Book(title="Sapiens", author="Yuval Noah Harari",
                isbn="978-0062316097", genre="Non-Fiction",
                description="A brief history of humankind."),
        Book(title="The Design of Everyday Things", author="Don Norman",
                isbn="978-0465050659", genre="Design",
                description="A powerful primer on how design serves as the communication between object and user."),
    ]

    for book in sample_books:
        db.session.add(book)

    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

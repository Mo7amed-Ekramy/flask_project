from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Book, Borrowing
from forms import RegisterForm, LoginForm, AddBookForm

main = Blueprint("main", __name__)


# ─── Auth Helpers ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        user = User.query.get(session["user_id"])
        if not user or not user.is_admin:
            flash("Administrator access required.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


# ─── Context Processor ────────────────────────────────────────────────────────

@main.context_processor
def inject_user():
    return {"current_user": current_user()}


# ─── Routes ──────────────────────────────────────────────────────────────────

@main.route("/")
def dashboard():
    user = current_user()
    total_books = Book.query.count()
    available_books = Book.query.filter_by(availability_status=True).count()
    total_users = User.query.filter_by(role="member").count() if user and user.is_admin else None
    active_borrowings = Borrowing.query.filter_by(status="borrowed").count()

    recent_books = Book.query.order_by(Book.added_at.desc()).limit(6).all()

    my_borrowings = []
    if user and not user.is_admin:
        my_borrowings = (
            Borrowing.query
            .filter_by(user_id=user.id, status="borrowed")
            .join(Book)
            .all()
        )

    return render_template(
        "index.html",
        total_books=total_books,
        available_books=available_books,
        total_users=total_users,
        active_borrowings=active_borrowings,
        recent_books=recent_books,
        my_borrowings=my_borrowings,
    )


@main.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html", form=form)

        user = User(username=username, email=email, role="member")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        password = form.password.data

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html", form=form)


@main.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@main.route("/books")
def books():
    search = request.args.get("q", "").strip()
    genre_filter = request.args.get("genre", "").strip()
    availability = request.args.get("availability", "all")

    query = Book.query

    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") | Book.author.ilike(f"%{search}%")
        )
    if genre_filter:
        query = query.filter(Book.genre == genre_filter)
    if availability == "available":
        query = query.filter_by(availability_status=True)
    elif availability == "borrowed":
        query = query.filter_by(availability_status=False)

    all_books = query.order_by(Book.title).all()
    genres = db.session.query(Book.genre).filter(Book.genre.isnot(None)).distinct().all()
    genres = [g[0] for g in genres]

    return render_template("books.html", books=all_books, genres=genres,
                            search=search, genre_filter=genre_filter, availability=availability)


@main.route("/books/add", methods=["GET", "POST"])
@admin_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        author = form.author.data.strip()
        isbn = form.isbn.data.strip()
        genre = form.genre.data.strip() if form.genre.data else None
        description = form.description.data.strip() if form.description.data else None

        if Book.query.filter_by(isbn=isbn).first():
            flash("A book with this ISBN already exists.", "danger")
            return render_template("add_book.html", form=form)

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            genre=genre,
            description=description,
            availability_status=True,
        )
        db.session.add(book)
        db.session.commit()
        flash(f'"{title}" has been added to the library.', "success")
        return redirect(url_for("main.books"))

    return render_template("add_book.html", form=form)


@main.route("/books/delete/<int:book_id>", methods=["POST"])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if not book.availability_status:
        flash("Cannot delete a book that is currently borrowed.", "danger")
        return redirect(url_for("main.books"))
    Borrowing.query.filter_by(book_id=book.id).delete()
    db.session.delete(book)
    db.session.commit()
    flash(f'"{book.title}" has been removed.', "info")
    return redirect(url_for("main.books"))


@main.route("/borrow/<int:book_id>", methods=["POST"])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    user = current_user()

    if user.is_admin:
        flash("Admins are not allowed to borrow books.", "danger")
        return redirect(url_for("main.books"))

    if not book.is_available:
        flash("This book is not available for borrowing.", "danger")
        return redirect(url_for("main.books"))

    active = Borrowing.query.filter_by(user_id=user.id, status="borrowed").count()
    if active >= 5:
        flash("You have reached the maximum limit of 5 borrowed books.", "warning")
        return redirect(url_for("main.books"))

    borrowing = Borrowing(
        user_id=user.id,
        book_id=book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status="borrowed",
    )
    book.availability_status = False

    db.session.add(borrowing)
    db.session.commit()
    flash(f'You borrowed "{book.title}". Due in 14 days.', "success")
    return redirect(url_for("main.my_borrowings"))


@main.route("/return/<int:borrowing_id>", methods=["POST"])
@login_required
def return_book(borrowing_id):
    borrowing = Borrowing.query.get_or_404(borrowing_id)
    user = current_user()

    if borrowing.user_id != user.id and not user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("main.dashboard"))

    if borrowing.status == "returned":
        flash("This book has already been returned.", "info")
        return redirect(url_for("main.my_borrowings"))

    borrowing.status = "returned"
    borrowing.return_date = datetime.utcnow()
    borrowing.book.availability_status = True

    db.session.commit()
    flash(f'"{borrowing.book.title}" returned successfully. Thank you!', "success")
    return redirect(url_for("main.my_borrowings"))


@main.route("/my-borrowings")
@login_required
def my_borrowings():
    user = current_user()
    if user.is_admin:
        return redirect(url_for("main.dashboard"))
    active = (
        Borrowing.query
        .filter_by(user_id=user.id, status="borrowed")
        .order_by(Borrowing.borrow_date.desc())
        .all()
    )
    history = (
        Borrowing.query
        .filter_by(user_id=user.id, status="returned")
        .order_by(Borrowing.return_date.desc())
        .all()
    )
    return render_template("my_borrowings.html", active=active, history=history, now=datetime.utcnow())


@main.route("/admin")
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    all_borrowings = (
        Borrowing.query
        .join(User).join(Book)
        .order_by(Borrowing.borrow_date.desc())
        .all()
    )
    overdue = [b for b in all_borrowings if b.is_overdue]
    return render_template("admin.html", users=users, all_borrowings=all_borrowings, overdue=overdue, now=datetime.utcnow())

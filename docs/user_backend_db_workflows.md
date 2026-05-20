# User to Backend to Database Workflows

This document describes every user-facing workflow in Librarium and how each action moves through the Flask backend and SQLite database.

## Main Components

| Layer | Files | Responsibility |
| --- | --- | --- |
| Browser UI | `templates/*.html`, `static/*` | Shows forms, lists, buttons, flash messages, and redirects |
| Routes / Controllers | `routes.py` | Receives HTTP requests, validates permissions, runs business rules, reads/writes database rows |
| Forms | `forms.py` | Validates submitted register, login, and add-book form fields |
| Models / Database | `models.py`, `library.db` | Stores users, books, and borrowing records through SQLAlchemy |
| App Setup | `app.py` | Creates Flask app, initializes SQLAlchemy, creates tables, seeds demo data |

## Database Tables

### `users`

Stores login accounts and roles.

Important fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary key used in sessions and borrowings |
| `username` | Unique username |
| `email` | Unique email |
| `password_hash` | Hashed password, never plain text |
| `role` | `admin` or `member` |
| `created_at` | Account creation time |

### `books`

Stores the library catalog.

Important fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary key used in URLs and borrowings |
| `title` | Book title |
| `author` | Book author |
| `isbn` | Unique ISBN |
| `genre` | Optional category |
| `description` | Optional description |
| `availability_status` | `True` means available, `False` means borrowed |
| `added_at` | Book creation time |

### `borrowings`

Stores every borrow/return transaction.

Important fields:

| Field | Purpose |
| --- | --- |
| `id` | Primary key used when returning a book |
| `user_id` | Foreign key to `users.id` |
| `book_id` | Foreign key to `books.id` |
| `borrow_date` | Date/time the book was borrowed |
| `due_date` | Usually 14 days after borrowing |
| `return_date` | Date/time the book was returned |
| `status` | `borrowed` or `returned` |

## Shared Authentication Workflows

### Current User Lookup

Used by dashboard, route guards, templates, borrow, return, and borrowing history.

1. Browser sends request with session cookie.
2. Backend checks whether `session["user_id"]` exists.
3. If present, backend runs:

   ```python
   User.query.get(session["user_id"])
   ```

4. The matching `users` row becomes the current user.
5. Templates receive `current_user` through the context processor.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user by primary key |

### Login Required Guard

Used by `/logout`, `/borrow/<book_id>`, `/return/<borrowing_id>`, and `/my-borrowings`.

1. Browser requests a protected route.
2. Backend checks if `user_id` exists in the Flask session.
3. If missing, backend flashes `Please log in to continue.`
4. Backend redirects to `/login`.
5. If present, backend continues to the requested route.

Database access:

| Table | Operation |
| --- | --- |
| None | Session-only check |

### Admin Required Guard

Used by `/books/add`, `/books/delete/<book_id>`, and `/admin`.

1. Browser requests an admin route.
2. Backend checks if `user_id` exists in the Flask session.
3. Backend loads the user from the `users` table.
4. Backend checks `user.role == "admin"`.
5. If not admin, backend flashes `Administrator access required.`
6. Backend redirects non-admin users to `/`.
7. If admin, backend continues to the requested route.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user by primary key |

## Public Workflows

## 1. View Dashboard

Route: `GET /`

Actors: Guest, member, admin

Backend flow:

1. Browser requests `/`.
2. Backend calls `current_user()`.
3. Backend counts all books.
4. Backend counts available books.
5. Backend counts active borrowings.
6. Backend loads the 6 most recently added books.
7. If the current user is an admin, backend counts member users.
8. If the current user is a member, backend loads that member's active borrowings.
9. Backend renders `templates/index.html`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user if logged in |
| `users` | Count member users for admin dashboard |
| `books` | Count all books |
| `books` | Count available books |
| `books` | Read 6 newest books |
| `borrowings` | Count active borrowings |
| `borrowings` | Read member's active borrowings |

Response:

| Result | Response |
| --- | --- |
| Success | Dashboard page |

## 2. Register Account

Route: `GET /register`

Actors: Guest

Backend flow:

1. Browser requests the registration page.
2. If already logged in, backend redirects to `/`.
3. Backend creates `RegisterForm`.
4. Backend renders `templates/register.html`.

Database access:

| Table | Operation |
| --- | --- |
| None | No database access on GET |

Route: `POST /register`

Actors: Guest

Backend flow:

1. Browser submits username, email, password, and confirm password.
2. Backend validates the form:
   - username is required and 3-80 characters
   - email is required and valid
   - password is required and at least 6 characters
   - confirm password must match password
3. Backend strips username.
4. Backend lowercases email.
5. Backend checks whether username already exists.
6. Backend checks whether email already exists.
7. Backend creates a `User` with `role="member"`.
8. Backend hashes the password with `user.set_password(password)`.
9. Backend inserts the user.
10. Backend commits the database transaction.
11. Backend flashes `Account created! Please log in.`
12. Backend redirects to `/login`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read by username to prevent duplicate username |
| `users` | Read by email to prevent duplicate email |
| `users` | Insert new member user |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Already logged in | Redirect to `/` |
| Invalid form | Re-render register page with validation errors |
| Duplicate username | Flash error and re-render register page |
| Duplicate email | Flash error and re-render register page |

## 3. Login

Route: `GET /login`

Actors: Guest

Backend flow:

1. Browser requests login page.
2. If already logged in, backend redirects to `/`.
3. Backend creates `LoginForm`.
4. Backend renders `templates/login.html`.

Database access:

| Table | Operation |
| --- | --- |
| None | No database access on GET |

Route: `POST /login`

Actors: Guest

Backend flow:

1. Browser submits username/email and password.
2. Backend validates required fields.
3. Backend searches `users` where:
   - `username == identifier`, or
   - `email == identifier.lower()`
4. If a user is found, backend verifies the submitted password against `password_hash`.
5. If valid, backend marks the session permanent.
6. Backend stores these session values:
   - `user_id`
   - `username`
   - `role`
7. Backend flashes a welcome message.
8. Backend redirects to `/`.
9. If invalid, backend flashes `Invalid credentials. Please try again.`
10. Backend re-renders `templates/login.html`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read by username or email |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Already logged in | Redirect to `/` |
| Invalid form | Re-render login page |
| Unknown user or wrong password | Flash error and re-render login page |

## 4. Browse, Search, and Filter Books

Route: `GET /books`

Actors: Guest, member, admin

Query parameters:

| Parameter | Purpose |
| --- | --- |
| `q` | Search title or author |
| `genre` | Filter by exact genre |
| `availability` | `all`, `available`, or `borrowed` |

Backend flow:

1. Browser requests `/books`.
2. Backend reads query parameters.
3. Backend starts a `Book.query`.
4. If `q` is present, backend filters title or author with case-insensitive matching.
5. If `genre` is present, backend filters exact genre.
6. If `availability=available`, backend filters `availability_status=True`.
7. If `availability=borrowed`, backend filters `availability_status=False`.
8. Backend orders matching books by title.
9. Backend loads all distinct genres for the filter menu.
10. Backend renders `templates/books.html`.

Database access:

| Table | Operation |
| --- | --- |
| `books` | Read filtered book list |
| `books` | Read distinct genres |

Response:

| Result | Response |
| --- | --- |
| Success | Books page with matching books and filter state |

## Member Workflows

## 5. Logout

Route: `GET /logout`

Actors: Logged-in member or admin

Backend flow:

1. Browser requests `/logout`.
2. `login_required` confirms a user is logged in.
3. Backend clears the Flask session.
4. Backend flashes `You have been logged out.`
5. Backend redirects to `/login`.

Database access:

| Table | Operation |
| --- | --- |
| None | Session-only workflow |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |

## 6. Borrow a Book

Route: `POST /borrow/<book_id>`

Actors: Logged-in member

Backend flow:

1. Browser submits borrow action for a book.
2. `login_required` confirms a user is logged in.
3. Backend loads the book by `book_id`.
4. Backend loads current user from session.
5. Backend rejects admins because admins cannot borrow books.
6. Backend checks `book.is_available`.
7. Backend counts active borrowings for the member where `status="borrowed"`.
8. Backend rejects the request if the member already has 5 active borrowings.
9. Backend creates a `Borrowing` row with:
   - `user_id`
   - `book_id`
   - `borrow_date=datetime.utcnow()`
   - `due_date=datetime.utcnow() + timedelta(days=14)`
   - `status="borrowed"`
10. Backend sets `book.availability_status=False`.
11. Backend inserts the borrowing row.
12. Backend commits the database transaction.
13. Backend flashes a due-date confirmation.
14. Backend redirects to `/my-borrowings`.

Database access:

| Table | Operation |
| --- | --- |
| `books` | Read book by primary key |
| `users` | Read current user by primary key |
| `borrowings` | Count member's active borrowings |
| `borrowings` | Insert new borrowing |
| `books` | Update availability to unavailable |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Book does not exist | 404 |
| User is admin | Flash error and redirect to `/books` |
| Book is already borrowed | Flash error and redirect to `/books` |
| Member has 5 active borrowings | Flash warning and redirect to `/books` |

## 7. Return a Book

Route: `POST /return/<borrowing_id>`

Actors: Logged-in member or admin

Backend flow:

1. Browser submits return action for a borrowing.
2. `login_required` confirms a user is logged in.
3. Backend loads the borrowing by `borrowing_id`.
4. Backend loads current user from session.
5. Backend allows the return only if:
   - borrowing belongs to the current user, or
   - current user is an admin
6. Backend checks whether borrowing is already returned.
7. Backend sets `borrowing.status="returned"`.
8. Backend sets `borrowing.return_date=datetime.utcnow()`.
9. Backend sets `borrowing.book.availability_status=True`.
10. Backend commits the database transaction.
11. Backend flashes success.
12. Backend redirects to `/my-borrowings`.

Database access:

| Table | Operation |
| --- | --- |
| `borrowings` | Read borrowing by primary key |
| `users` | Read current user by primary key |
| `borrowings` | Update status and return date |
| `books` | Update availability to available |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Borrowing does not exist | 404 |
| Borrowing belongs to another member and current user is not admin | Flash error and redirect to `/` |
| Borrowing already returned | Flash info and redirect to `/my-borrowings` |

Note: Admins are allowed to return a borrowing, but the route still redirects to `/my-borrowings`. Since admins are redirected away from `/my-borrowings`, this may result in an extra redirect to `/`.

## 8. View My Borrowings

Route: `GET /my-borrowings`

Actors: Logged-in member

Backend flow:

1. Browser requests `/my-borrowings`.
2. `login_required` confirms a user is logged in.
3. Backend loads current user from session.
4. If current user is admin, backend redirects to `/`.
5. Backend loads active borrowings for the member where `status="borrowed"`, newest first.
6. Backend loads returned borrowings for the member where `status="returned"`, newest return first.
7. Backend passes `datetime.utcnow()` as `now` for overdue display logic.
8. Backend renders `templates/my_borrowings.html`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user by primary key |
| `borrowings` | Read member's active borrowings |
| `borrowings` | Read member's returned borrowing history |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Current user is admin | Redirect to `/` |

## Admin Workflows

## 9. Add a Book

Route: `GET /books/add`

Actors: Admin

Backend flow:

1. Browser requests the add-book page.
2. `admin_required` confirms the user is logged in and has `role="admin"`.
3. Backend creates `AddBookForm`.
4. Backend renders `templates/add_book.html`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user during admin guard |

Route: `POST /books/add`

Actors: Admin

Backend flow:

1. Browser submits title, author, ISBN, optional genre, and optional description.
2. `admin_required` confirms admin access.
3. Backend validates the form:
   - title is required and max 200 characters
   - author is required and max 150 characters
   - ISBN is required and max 20 characters
   - genre is optional and max 80 characters
   - description is optional
4. Backend strips submitted text values.
5. Backend checks whether ISBN already exists.
6. Backend creates a `Book` with `availability_status=True`.
7. Backend inserts the book.
8. Backend commits the database transaction.
9. Backend flashes a success message.
10. Backend redirects to `/books`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user during admin guard |
| `books` | Read by ISBN to prevent duplicate ISBN |
| `books` | Insert new book |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Not admin | Flash error and redirect to `/` |
| Invalid form | Re-render add-book page |
| Duplicate ISBN | Flash error and re-render add-book page |

## 10. Delete a Book

Route: `POST /books/delete/<book_id>`

Actors: Admin

Backend flow:

1. Browser submits delete action for a book.
2. `admin_required` confirms admin access.
3. Backend loads the book by `book_id`.
4. Backend checks `book.availability_status`.
5. If the book is currently borrowed, backend blocks deletion.
6. Backend deletes old borrowing records for the book.
7. Backend deletes the book.
8. Backend commits the database transaction.
9. Backend flashes removal confirmation.
10. Backend redirects to `/books`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user during admin guard |
| `books` | Read book by primary key |
| `borrowings` | Delete borrowing history for that book |
| `books` | Delete book |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Not admin | Flash error and redirect to `/` |
| Book does not exist | 404 |
| Book is currently borrowed | Flash error and redirect to `/books` |

## 11. View Admin Panel

Route: `GET /admin`

Actors: Admin

Backend flow:

1. Browser requests `/admin`.
2. `admin_required` confirms admin access.
3. Backend loads all users, newest first.
4. Backend loads all borrowings joined with their user and book, newest borrowings first.
5. Backend computes overdue borrowings in Python using `Borrowing.is_overdue`.
6. Backend passes `datetime.utcnow()` as `now`.
7. Backend renders `templates/admin.html`.

Database access:

| Table | Operation |
| --- | --- |
| `users` | Read current user during admin guard |
| `users` | Read all users |
| `borrowings` | Read all borrowings |
| `books` | Joined while reading borrowing book data |

Failure paths:

| Condition | Backend response |
| --- | --- |
| Not logged in | Redirect to `/login` |
| Not admin | Flash error and redirect to `/` |

## Startup and Seed Workflow

Route: Application startup through `create_app()`

Backend flow:

1. Flask application is created.
2. Configuration is loaded from `config.py`.
3. SQLAlchemy is initialized.
4. Main blueprint from `routes.py` is registered.
5. Inside the application context, backend calls `db.create_all()`.
6. Backend calls `_seed_data()`.
7. If any user already exists, seeding stops.
8. If no user exists, backend creates:
   - admin user: `admin@library.dev` / `admin123`
   - member user: `alice@library.dev` / `alice123`
   - 6 sample books
9. Backend commits seed data.

Database access:

| Table | Operation |
| --- | --- |
| All model tables | Create missing tables |
| `users` | Check whether seed data already exists |
| `users` | Insert demo admin and member |
| `books` | Insert sample books |

## Workflow Summary Matrix

| Workflow | Route | Actor | Database Reads | Database Writes |
| --- | --- | --- | --- | --- |
| Dashboard | `GET /` | Guest/member/admin | users, books, borrowings | None |
| Register | `POST /register` | Guest | users | users insert |
| Login | `POST /login` | Guest | users | None |
| Logout | `GET /logout` | Logged-in user | None | None |
| Browse books | `GET /books` | Guest/member/admin | books | None |
| Add book | `POST /books/add` | Admin | users, books | books insert |
| Delete book | `POST /books/delete/<book_id>` | Admin | users, books | borrowings delete, books delete |
| Borrow book | `POST /borrow/<book_id>` | Member | users, books, borrowings | borrowings insert, books update |
| Return book | `POST /return/<borrowing_id>` | Member/admin | users, borrowings, books | borrowings update, books update |
| My borrowings | `GET /my-borrowings` | Member | users, borrowings | None |
| Admin panel | `GET /admin` | Admin | users, borrowings, books | None |

## Important Business Rules

1. New registered users are always created as `member`.
2. Admin users can manage books and view all users/borrowings.
3. Admin users cannot borrow books.
4. Members can borrow only available books.
5. Members can have a maximum of 5 active borrowed books.
6. Borrowed books get a due date 14 days after borrowing.
7. Returning a book marks the borrowing as `returned` and makes the book available again.
8. A book cannot be deleted while it is currently borrowed.
9. Deleting an available book also deletes its old borrowing history.
10. Overdue status is computed dynamically from `due_date`; it is not automatically written to the database.

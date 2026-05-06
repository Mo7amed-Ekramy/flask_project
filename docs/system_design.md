# System Design — Librarium

## Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    USER {
        int     id          PK
        string  username    "UNIQUE NOT NULL"
        string  email       "UNIQUE NOT NULL"
        string  password_hash
        string  role        "admin | member"
        datetime created_at
    }

    BOOK {
        int     id          PK
        string  title
        string  author
        string  isbn        "UNIQUE NOT NULL"
        string  genre
        text    description
        bool    availability_status  "True=available"
        datetime added_at
    }

    BORROWING {
        int     id          PK
        int     user_id     FK
        int     book_id     FK
        datetime borrow_date
        datetime due_date
        datetime return_date
        string  status      "borrowed | returned | overdue"
    }

    USER ||--o{ BORROWING : "creates"
    BOOK ||--o{ BORROWING : "is tracked by"
```

---

## Data Flow Diagram (DFD) — Level 0 (Context Diagram)

```mermaid
flowchart TD
    Member([👤 Member])
    Admin([🛡 Admin])
    LMS[[Librarium\nSystem]]
    DB[(SQLite DB)]

    Member -- "Register / Login" --> LMS
    Member -- "Browse & Search Books" --> LMS
    Member -- "Borrow / Return Book" --> LMS
    LMS -- "Loan Status & History" --> Member

    Admin -- "Login" --> LMS
    Admin -- "Add / Delete Books" --> LMS
    Admin -- "View All Loans & Users" --> LMS
    Admin -- "Mark Book Returned" --> LMS
    LMS -- "Reports & Overdue Alerts" --> Admin

    LMS -- "Read / Write" --> DB
    DB -- "Query Results" --> LMS
```

---

## Data Flow Diagram (DFD) — Level 1 (Internal Processes)

```mermaid
flowchart LR
    subgraph Client
        U([User Browser])
    end

    subgraph Flask Application
        direction TB
        P1[1.0\nAuthentication\nRegister / Login / Logout]
        P2[2.0\nBook Management\nBrowse / Add / Delete]
        P3[3.0\nBorrowing Engine\nBorrow / Return]
        P4[4.0\nAdmin Dashboard\nUsers & Loan Reports]
    end

    subgraph Database
        D1[(Users Table)]
        D2[(Books Table)]
        D3[(Borrowings Table)]
    end

    U -- "POST /register\nPOST /login" --> P1
    P1 -- "Store / Verify credentials" --> D1
    P1 -- "Session token" --> U

    U -- "GET /books\nPOST /books/add" --> P2
    P2 -- "Query / Insert / Delete" --> D2
    P2 -- "Book list / confirmation" --> U

    U -- "POST /borrow/<id>\nPOST /return/<id>" --> P3
    P3 -- "Check availability" --> D2
    P3 -- "Create / Update borrowing" --> D3
    P3 -- "Update availability flag" --> D2
    P3 -- "Loan confirmation" --> U

    U -- "GET /admin" --> P4
    P4 -- "Read all users" --> D1
    P4 -- "Read all borrowings" --> D3
    P4 -- "Dashboard data" --> U
```

---

## Sequence Diagram — Borrow a Book

```mermaid
sequenceDiagram
    actor Member
    participant Browser
    participant Flask
    participant DB

    Member->>Browser: Click "Borrow" on book card
    Browser->>Flask: POST /borrow/<book_id>
    Flask->>Flask: Verify session (login_required)
    Flask->>DB: SELECT book WHERE id=book_id
    DB-->>Flask: Book record
    Flask->>Flask: Check availability_status == True
    Flask->>DB: SELECT COUNT borrowings WHERE user_id AND status='borrowed'
    DB-->>Flask: active loan count
    Flask->>Flask: Check count < 5
    Flask->>DB: INSERT INTO borrowings (user_id, book_id, borrow_date, due_date, status='borrowed')
    Flask->>DB: UPDATE books SET availability_status=False WHERE id=book_id
    DB-->>Flask: Commit OK
    Flask-->>Browser: Redirect /my-borrowings + Flash "Borrowed!"
    Browser-->>Member: My Books page with active loan
```

---

## Folder Structure

```
librarium/
├── app.py                  # Application factory & entry point
├── config.py               # Config classes (Dev / Prod)
├── models.py               # SQLAlchemy models: User, Book, Borrowing
├── routes.py               # All Blueprint routes
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── library.db              # Auto-generated SQLite database
├── templates/
│   ├── base.html           # Master layout (nav, flash messages, footer)
│   ├── index.html          # Dashboard / Home
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── books.html          # Book listing with search & filters
│   ├── add_book.html       # Add new book form (admin)
│   ├── my_borrowings.html  # User's active & past loans
│   └── admin.html          # Admin panel (users + all borrowings)
└── docs/
    └── system_design.md    # This file
```

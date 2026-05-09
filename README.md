# 📚 Librarium — Library Management System

A simple and functional Flask web application for managing a digital library. Features a dark, minimal aesthetic, role-based access control, full borrowing lifecycle management, and a clean REST-style routing structure.

---

## 👥 Team Members

1. Mohamed Ekramy
2. Mahmoud Sayed
3. Mohamed El Motaz
4. Tammer yasser
5. Alla Mamdouh
6. Julia Osama

---

## ✨ Features

| Feature               | Details                                                  |
| --------------------- | -------------------------------------------------------- |
| **Authentication**    | Register, login, logout with hashed passwords (Werkzeug) |
| **Role-based Access** | `admin` and `member` roles with route guards             |
| **Book Management**   | Add, browse, search, filter, and delete books            |
| **Borrowing System**  | Borrow & return books with due dates (14-day window)     |
| **Admin Dashboard**   | User list, all borrowings, overdue loan alerts           |
| **Dark UI**           | Custom dark theme with Playfair Display typography       |
| **Seeded Demo Data**  | Admin + member account + 6 sample books on first run     |
| **Docker Ready**      | Dockerfile + docker-compose for one-command deployment   |

---

## 🗂 Folder Structure

```
librarium/
├── app.py                  # Application factory & entry point
├── config.py               # Configuration classes
├── models.py               # SQLAlchemy models (User, Book, Borrowing)
├── routes.py               # All Flask routes (Blueprint)
├── requirements.txt        # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── templates/
│   ├── base.html           # Shared layout
│   ├── index.html          # Dashboard
│   ├── login.html
│   ├── register.html
│   ├── books.html          # Book catalogue
│   ├── add_book.html       # Admin: add book
│   ├── my_borrowings.html  # Member: loan history
│   └── admin.html          # Admin panel
└── docs/
    └── system_design.md    # ERD, DFD, Sequence Diagrams (Mermaid)
```

---

## 🚀 Running Locally

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/librarium.git
cd librarium

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

The app will be available at **http://localhost:5000**

---

## 🐳 Running with Docker

```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down
```

The app will be available at **http://localhost:5000**

---

## 🔑 Default Credentials (Seeded on First Run)

| Role   | Username | Password   |
| ------ | -------- | ---------- |
| Admin  | `admin`  | `admin123` |
| Member | `alice`  | `alice123` |

> **Change these immediately in production!**

---

## 🌐 Endpoints

| Method | Route                    | Auth           | Description                             |
| ------ | ------------------------ | -------------- | --------------------------------------- |
| GET    | `/`                      | Public         | Dashboard / Home                        |
| GET    | `/register`              | Public         | Registration form                       |
| POST   | `/register`              | Public         | Create new member account               |
| GET    | `/login`                 | Public         | Login form                              |
| POST   | `/login`                 | Public         | Authenticate user                       |
| GET    | `/logout`                | Member         | End session                             |
| GET    | `/books`                 | Public         | Browse all books (with search & filter) |
| GET    | `/books/add`             | Admin          | Add book form                           |
| POST   | `/books/add`             | Admin          | Submit new book                         |
| POST   | `/books/delete/<id>`     | Admin          | Delete a book                           |
| POST   | `/borrow/<book_id>`      | Member         | Borrow a book                           |
| POST   | `/return/<borrowing_id>` | Member / Admin | Return a borrowed book                  |
| GET    | `/my-borrowings`         | Member         | View personal loans                     |
| GET    | `/admin`                 | Admin          | Admin panel                             |

---

## 🗄 Database Schema

### `users`

| Column        | Type         | Notes               |
| ------------- | ------------ | ------------------- |
| id            | INTEGER      | PK                  |
| username      | VARCHAR(80)  | UNIQUE              |
| email         | VARCHAR(120) | UNIQUE              |
| password_hash | VARCHAR(256) | Werkzeug hash       |
| role          | VARCHAR(20)  | `admin` or `member` |
| created_at    | DATETIME     | Auto                |

### `books`

| Column              | Type         | Notes            |
| ------------------- | ------------ | ---------------- |
| id                  | INTEGER      | PK               |
| title               | VARCHAR(200) |                  |
| author              | VARCHAR(150) |                  |
| isbn                | VARCHAR(20)  | UNIQUE           |
| genre               | VARCHAR(80)  | Optional         |
| description         | TEXT         | Optional         |
| availability_status | BOOLEAN      | True = available |
| added_at            | DATETIME     | Auto             |

### `borrowings`

| Column      | Type        | Notes                   |
| ----------- | ----------- | ----------------------- |
| id          | INTEGER     | PK                      |
| user_id     | INTEGER     | FK → users.id           |
| book_id     | INTEGER     | FK → books.id           |
| borrow_date | DATETIME    | Auto                    |
| due_date    | DATETIME    | +14 days                |
| return_date | DATETIME    | Set on return           |
| status      | VARCHAR(20) | `borrowed` / `returned` |

---

## 🔒 Security Notes

- Passwords are hashed with `werkzeug.security.generate_password_hash` (scrypt)
- Admin routes protected with `@admin_required` decorator
- Session-based authentication with `PERMANENT_SESSION_LIFETIME = 2 hours`
- **Before going to production:** change `SECRET_KEY` to a cryptographically random value

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📐 System Design

See [`docs/system_design.md`](docs/system_design.md) for:

- Entity-Relationship Diagram (ERD)
- Data Flow Diagram — Level 0 (Context)
- Data Flow Diagram — Level 1 (Internal Processes)
- Sequence Diagram (Borrow Flow)

All diagrams are written in **Mermaid.js** syntax — render them on [mermaid.live](https://mermaid.live) or in any Markdown viewer that supports Mermaid.

# Financial Tracking App

A multi-user finance tracking application that allows users to manage their income and expenses with support for **Global Categories** (visible to all users) and **Custom Categories** (user-specific).

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | FastAPI (Python 3.10+)                          |
| Database   | PostgreSQL with Raw SQL (asyncpg, no ORM)       |
| Frontend   | Vue 3 (Composition API), Vite, Pinia, Axios     |
| Styling    | TailwindCSS                                     |
| Auth       | OAuth2 with JWT (python-jose, passlib)          |

---

## Prerequisites

Before setting up this project, ensure you have the following installed:

| Requirement     | Description                                           |
|-----------------|-------------------------------------------------------|
| **PostgreSQL**  | Database server (v12 or higher recommended)           |
| **Conda**       | Anaconda/Miniconda with the `pacmann` environment     |
| **Node.js**     | v18+ with npm (for frontend)                          |

---

## Backend Setup

### Step 1: Navigate to the Project Directory

```bash
cd /path/to/FinanceTrackingApp
```

### Step 3: Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and configure your database connection:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/finance_db
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**DATABASE_URL Format:**

```
postgresql://<username>:<password>@<host>:<port>/<database_name>
```

| Component   | Example          | Description                    |
|-------------|------------------|--------------------------------|
| username    | `postgres`       | PostgreSQL username            |
| password    | `mypassword`     | PostgreSQL password            |
| host        | `localhost`      | Database server host           |
| port        | `5432`           | PostgreSQL port (default 5432) |
| database    | `finance_db`     | Target database name           |

> **Note:** Create the database in PostgreSQL before proceeding:
>
> ```sql
> CREATE DATABASE finance_db;
> ```

### Step 5: Initialize the Database

Since this project uses **Raw SQL** (no ORM like SQLAlchemy or migration tools like Alembic), you must manually run the initialization script to:

- Create all required tables
- Seed default global categories

```bash
python backend/app/db/init_db.py
```

**Expected Output:**

```
Connecting to database...
Creating tables...
Tables created successfully!
Seeding default categories...
Seeded 15 default categories!
Database initialization complete!
```

### Step 6: Run the Backend Server

```bash
conda activate pacmann
uvicorn backend.main:app --reload
```

The API will be available at: **<http://localhost:8000>**

---

## Frontend Setup

### Step 1: Navigate to the Frontend Directory

```bash
cd frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

### Step 3: Start the Development Server

```bash
npm run dev
```

The frontend will be available at: **<http://localhost:5173>**

---

## API Documentation

Once the backend server is running, interactive API documentation is available via **Swagger UI**:

| Documentation | URL                            |
|---------------|--------------------------------|
| Swagger UI    | <http://localhost:8000/docs>     |
| ReDoc         | <http://localhost:8000/redoc>    |

### Available Endpoints

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| POST   | `/auth/register`      | Register a new user                  |
| POST   | `/auth/token`         | Login and get JWT token              |
| GET    | `/auth/me`            | Get current user info                |
| GET    | `/wallets`            | List user's wallets                  |
| POST   | `/wallets`            | Create a new wallet                  |
| GET    | `/categories`         | List global + user's custom categories |
| POST   | `/categories`         | Create a custom category             |
| GET    | `/transactions`       | List user's transactions             |
| POST   | `/transactions`       | Create a new transaction             |
| GET    | `/transactions/summary` | Get income/expense summary         |
| DELETE | `/transactions/{id}`  | Delete a transaction                 |

---

## Project Structure

```
FinanceTrackingApp/
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Environment template
├── README.md                   # This file
│
├── backend/
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application entry point
│   └── app/
│       ├── core/
│       │   ├── config.py       # Settings from .env
│       │   ├── database.py     # asyncpg connection pool
│       │   └── security.py     # JWT & password utilities
│       ├── db/
│       │   ├── schema.sql      # DDL for all tables
│       │   └── init_db.py      # Database initialization script
│       ├── repositories/       # Raw SQL data access layer
│       │   ├── user_repo.py
│       │   ├── wallet_repo.py
│       │   ├── category_repo.py
│       │   └── transaction_repo.py
│       ├── routers/            # API route handlers
│       │   ├── auth.py
│       │   ├── wallets.py
│       │   ├── categories.py
│       │   └── transactions.py
│       └── schemas/            # Pydantic request/response models
│           ├── user.py
│           ├── wallet.py
│           ├── category.py
│           └── transaction.py
│
└── frontend/
    ├── package.json            # Node dependencies
    ├── vite.config.js          # Vite configuration
    ├── tailwind.config.js      # TailwindCSS configuration
    ├── index.html              # HTML entry point
    └── src/
        ├── main.js             # Vue app initialization
        ├── App.vue             # Root component
        ├── style.css           # Tailwind imports
        ├── api/
        │   └── index.js        # Axios instance with JWT interceptor
        ├── stores/
        │   ├── auth.js         # Authentication state (Pinia)
        │   └── finance.js      # Finance data state (Pinia)
        ├── router/
        │   └── index.js        # Vue Router configuration
        └── views/
            ├── LoginView.vue
            ├── RegisterView.vue
            ├── DashboardView.vue
            └── AddTransactionView.vue
```

---

## Quick Start Summary

```bash
# Terminal 1 - Backend
conda activate pacmann
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env with your database credentials
python backend/app/db/init_db.py
uvicorn backend.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

---

## Default Categories

The initialization script seeds the following **global categories**:

**Income Categories:**

- Gaji (Salary)
- Bonus
- Hadiah (Gift)
- Investasi (Investment)
- Penjualan (Sales)
- Lainnya (Others)

**Expense Categories:**

- Makanan (Food)
- Transportasi (Transportation)
- Tagihan (Bills)
- Belanja (Shopping)
- Hiburan (Entertainment)
- Kesehatan (Health)
- Pendidikan (Education)
- Cicilan (Installments)
- Donasi (Donation)

# FinanceTracker - Personal Finance Manager

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue_3-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

A modern, high-performance personal finance management application designed to help users take control of their financial life. Built with **FastAPI** backend using Raw SQL queries for maximum performance and **Vue 3** frontend for a responsive user experience.

## Why FinanceTracker?

- **Multiple Wallets** — Manage cash, bank accounts, and e-wallets in one place
- **Smart Categorization** — Track expenses and income with global or custom categories
- **Wallet Transfers** — Move funds between wallets without affecting expense reports
- **Visual Analytics** — Understand spending patterns with interactive charts
- **Professional Reports** — Export transactions to Excel with accounting-style formatting
- **Multi-User Ready** — Secure authentication with admin panel for user management

---

## Table of Contents

- [FinanceTracker - Personal Finance Manager](#financetracker---personal-finance-manager)
  - [Why FinanceTracker?](#why-financetracker)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Tech Stack](#tech-stack)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Database](#database)
    - [DevOps](#devops)
  - [⚡ Performance \& Architecture](#-performance--architecture)
    - [Why This Stack is Fast](#why-this-stack-is-fast)
    - [Benchmark Context](#benchmark-context)
    - [Architecture Diagram](#architecture-diagram)
  - [Installation Guide](#installation-guide)
    - [Prerequisites](#prerequisites)
    - [Step 1: Database Setup](#step-1-database-setup)
    - [Step 2: Backend Setup](#step-2-backend-setup)
    - [Step 3: Frontend Setup](#step-3-frontend-setup)
  - [Usage Guide](#usage-guide)
    - [Running the Backend](#running-the-backend)
    - [Running the Frontend](#running-the-frontend)
  - [Deployment with Docker](#deployment-with-docker)
    - [Quick Start](#quick-start)
    - [Docker Commands Reference](#docker-commands-reference)
  - [🔌 API Examples](#-api-examples)
    - [Authentication](#authentication)
    - [Create Transaction](#create-transaction)
    - [Transfer Between Wallets](#transfer-between-wallets)
  - [❓ Troubleshooting](#-troubleshooting)
    - [Database Connection Issues](#database-connection-issues)
    - [Missing Tables](#missing-tables)
    - [CORS Errors](#cors-errors)
    - [JWT Token Expired](#jwt-token-expired)
    - [Docker Build Fails](#docker-build-fails)
  - [Project Structure](#project-structure)

---

## Key Features

| Feature | Description |
|---------|-------------|
| **High Performance** | Uses `asyncpg` with Raw SQL queries — no ORM overhead for maximum speed. |
| **Dual-Category System** | Supports both Global (public) and Custom (private) categories per user. |
| **Atomic Transactions** | Wallet-to-wallet transfers with atomic database operations ensure data integrity. |
| **Smart Analytics** | Interactive charts that automatically filter out internal transfers for accurate insights. |
| **Excel Export** | Generate accounting-format Excel reports with proper currency formatting. |
| **Multi-User Support** | Secure JWT authentication with role-based access (Admin & User). |

---

## Tech Stack

### Backend

- **Framework:** FastAPI
- **Language:** Python 3.10+
- **Database Driver:** asyncpg (async PostgreSQL)
- **Validation:** Pydantic v2
- **Authentication:** OAuth2 with JWT tokens

### Frontend

- **Framework:** Vue 3 (Composition API)
- **Build Tool:** Vite
- **State Management:** Pinia
- **Styling:** TailwindCSS
- **Charts:** Chart.js + vue-chartjs

### Database

- **PostgreSQL 14+**

### DevOps

- **Docker & Docker Compose**

---

## ⚡ Performance & Architecture

### Why This Stack is Fast

FinanceTracker is built for speed using a high-performance async architecture:

| Component | Technology | Advantage |
|-----------|------------|-----------|
| **Web Framework** | FastAPI | Async/await native, one of the fastest Python frameworks |
| **Database Driver** | asyncpg | Direct PostgreSQL protocol, no ORM overhead |
| **Query Strategy** | Raw SQL | Zero abstraction layer, maximum query control |
| **Connection Pool** | asyncpg.Pool | Persistent connections, minimal latency |

### Benchmark Context

| Driver | Relative Speed | Notes |
|--------|----------------|-------|
| `asyncpg` | **~3x faster** | Direct binary protocol, zero-copy data |
| `psycopg2` | Baseline | Synchronous, text protocol |
| SQLAlchemy ORM | ~2-5x slower | Object mapping overhead |

> **Expected Latency:** API read operations typically respond in **< 10ms** on local networks. Write operations with atomic transactions average **15-25ms**.

### Architecture Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vue 3     │────▶│   FastAPI   │────▶│ PostgreSQL  │
│  Frontend   │ API │   Backend   │ SQL │  Database   │
│   (Nginx)   │◀────│  (Uvicorn)  │◀────│  (asyncpg)  │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   │
       │              JWT Auth
       └───────────────────┘
```

---

## Installation Guide

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.10 or higher** — [Download Python](https://www.python.org/downloads/)
- **Node.js 18 or higher** — [Download Node.js](https://nodejs.org/)
- **PostgreSQL 14 or higher** — [Download PostgreSQL](https://www.postgresql.org/download/)

---

### Step 1: Database Setup

1. **Create a new PostgreSQL database:**

   Open your terminal or PostgreSQL client and run:

   ```sql
   CREATE DATABASE finance_db;
   ```

2. **Configure environment variables:**

   Create a `.env` file in the project root directory. You can use the following template:

   ```env
   # Database Configuration
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/finance_db

   # JWT Configuration
   SECRET_KEY=your-super-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Admin Credentials (created automatically on first run)
   ADMIN_EMAIL=your_email
   ADMIN_USERNAME=your_username
   ADMIN_PASSWORD=your_password
   ```

   > **Note:** Replace `your_password` with your actual PostgreSQL password and `your-super-secret-key-here` with a secure random string.

---

### Step 2: Backend Setup

1. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv fintrack_env
   ```

3. **Activate the virtual environment:**

   **Windows:**

   ```cmd
   .\fintrack_env\Scripts\activate
   ```

   **macOS / Linux:**

   ```bash
   source fintrack_env/bin/activate
   ```

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database:**

   This script will create all necessary tables and seed default data (including the admin user):

   ```bash
   python app/db/init_db.py
   ```

   You should see output similar to:

   ```
   Connecting to database...
   Creating tables...
   Tables created successfully!
   Seeded 15 default categories!
   Superuser created: admin@example.com
   Database initialization complete!
   ```

---

### Step 3: Frontend Setup

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start the development server:**

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`.

---

## Usage Guide

### Running the Backend

From the `backend` directory (with your virtual environment activated):

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.

- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

### Running the Frontend

From the `frontend` directory:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Deployment with Docker

The easiest way to run the full stack is using Docker Compose.

### Quick Start

1. **Build and start all services:**

   ```bash
   docker-compose up --build -d
   ```

2. **Initialize the database (first time only):**

   ```bash
   docker-compose exec backend python -m backend.app.db.init_db
   ```

3. **Access the application:**

   | Service | URL |
   |---------|-----|
   | **Frontend** | <http://localhost> |
   | **Backend API** | <http://localhost:8000> |
   | **API Docs** | <http://localhost:8000/docs> |

### Docker Commands Reference

```bash
# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (reset database)
docker-compose down -v

# Rebuild a specific service
docker-compose build backend
```

---

## 🔌 API Examples

Base URL: `http://localhost:8000`

### Authentication

**Login and get JWT token:**

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=YourPassword123"
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Note:** A `refresh_token` is also set as an HTTPOnly cookie for automatic token renewal.

---

### Create Transaction

```bash
curl -X POST "http://localhost:8000/transactions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_id": 1,
    "category_id": 5,
    "amount": 150000,
    "type": "EXPENSE",
    "description": "Grocery shopping",
    "transaction_date": "2024-01-15"
  }'
```

**Response:**

```json
{
  "id": 42,
  "wallet_id": 1,
  "category_id": 5,
  "amount": "150000.00",
  "type": "EXPENSE",
  "description": "Grocery shopping",
  "transaction_date": "2024-01-15",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### Transfer Between Wallets

```bash
curl -X POST "http://localhost:8000/transactions/transfer" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_wallet_id": 1,
    "dest_wallet_id": 2,
    "amount": 500000,
    "description": "Transfer to savings"
  }'
```

**Response:**

```json
{
  "message": "Transfer successful",
  "amount": "500000.00",
  "source_wallet": "Main Wallet",
  "dest_wallet": "Savings Account"
}
```

> **Atomic Operation:** This endpoint creates two transaction records (EXPENSE + INCOME) within a single database transaction, ensuring data integrity.

---

For complete API documentation, visit: `http://localhost:8000/docs`

---

## ❓ Troubleshooting

### Database Connection Issues

**Problem:** `Connection Refused` or `could not connect to server`

```
asyncpg.exceptions.ConnectionRefusedError: 
  could not connect to server: Connection refused
```

**Solutions:**

1. Ensure PostgreSQL is running:

   ```bash
   # Docker
   docker-compose ps
   
   # Local PostgreSQL
   sudo systemctl status postgresql
   ```

2. Verify `DATABASE_URL` in your `.env` file matches your setup
3. Check if the port (default 5432) is not blocked by firewall

---

### Missing Tables

**Problem:** `relation "users" does not exist` or `Table not found`

```
asyncpg.exceptions.UndefinedTableError: 
  relation "users" does not exist
```

**Solution:** Initialize the database schema manually:

```bash
# Local development
cd backend
python app/db/init_db.py

# Docker
docker-compose exec backend python -m backend.app.db.init_db
```

> **Why this happens:** This project uses Raw SQL instead of an ORM, so there are no automatic migrations. You must run the init script to create tables.

---

### CORS Errors

**Problem:** `Access to XMLHttpRequest blocked by CORS policy`

```
Access to XMLHttpRequest at 'http://localhost:8000/...' 
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solutions:**

1. Add your frontend URL to `.env`:

   ```env
   BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
   ```

2. Restart the backend server after changing `.env`
3. For Docker, ensure the frontend service name is correct in CORS origins

---

### JWT Token Expired

**Problem:** `401 Unauthorized` after some time

**Solution:** The access token expires after 15 minutes. The frontend automatically refreshes tokens using the HTTPOnly cookie. If issues persist:

1. Clear browser cookies and localStorage
2. Login again to get fresh tokens
3. Check if `refresh_token` cookie is being set (requires `withCredentials: true` in Axios)

---

### Docker Build Fails

**Problem:** `ModuleNotFoundError` or missing dependencies

**Solutions:**

1. Rebuild without cache:

   ```bash
   docker-compose build --no-cache
   ```

2. Remove old volumes and restart:

   ```bash
   docker-compose down -v
   docker-compose up --build -d
   ```

---

## Project Structure

```
FinanceTrackingApp/
├── backend/
│   ├── app/
│   │   ├── core/          # Security, database connection
│   │   ├── db/            # Schema, migrations, init scripts
│   │   ├── repositories/  # Raw SQL data access layer
│   │   ├── routers/       # API endpoints
│   │   └── schemas/       # Pydantic models
│   ├── main.py            # FastAPI application entry
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios configuration
│   │   ├── components/    # Reusable Vue components
│   │   ├── stores/        # Pinia state management
│   │   ├── views/         # Page components
│   │   └── router/        # Vue Router configuration
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .env
```

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

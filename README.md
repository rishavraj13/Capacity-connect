# Capacity Connect - Backend Portal

Capacity Connect is a Django-based learning management and capacity-building portal.

## Local Setup

1. **Clone and checkout phase branch:**
   ```bash
   git checkout phase/b0-foundations
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows PowerShell
   ```

3. **Install pinned dependencies:**
   ```bash
   pip install -r requirements/dev.txt
   ```

4. **Prepare environment configuration:**
   ```bash
   cp .env.example .env
   ```

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Execute test suite:**
   ```bash
   pytest
   ```

7. **Code quality checks:**
   ```bash
   ruff check .
   ruff format --check .
   ```

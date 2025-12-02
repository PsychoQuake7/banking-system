

# Banking System (Django)

A collaborative Django-based banking system with modules for accounts, ledger, loans, transactions and notifications. Includes management scripts for seeding test data and creating admin/test users, plus a comprehensive test suite.

---

## 🚀 Highlights / Features

- Role-based user management and officer/admin actions  
- Account management: balances, deposits, withdrawals, transfers  
- Ledger & transaction accounting (double-entry style components)  
- Loan module: applications, interest calculation, approval flows  
- Notifications: email/in-app notifications for transactions / reminders  
- Management scripts: `create_admin.py`, `setup_test_data.py`, `create_browser_test_users.py`  
- Tests: `tests/` directory contains multiple test modules (loans, transactions, reminders, staff verification, etc.)

---

## Repo layout (top-level)

├── accounts/# user & profilemodels, auth logic    ├── audit/# auditing / change logs 
├── clients/# client/customer models & views
├── docs/# documentation 
├── kayamanan/# domain/business logic
├── ledger/# ledger / accounting logic 
├── loans/# loan processing & interest 
├── notifications/# notification senders/templates 
├── static/
│   └── css/# static assets 
├── templates/# html templates & error pages 
├── tests/# unit / integration tests 
├── transactions/# transaction engine / processing ├── users/# user management
├── utils/# helper utilities 
├── manage.py 
├── requirements.txt 
├── setup_test_data.py 
├── create_admin.py 
├── create_browser_test_users.py 
├── STAFF_MANUAL_TEST.md 
└── README.md

---

## 🛠️ Local development — Getting started

> Prereqs: Python 3.8+ (or compatible), pip, virtualenv

1. Clone the repository  
   ```bash
   git clone https://github.com/PsychoQuake7/banking-system.git
   cd banking-system

2. Create & activate a virtualenv

python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate


3. Install dependencies

pip install -r requirements.txt


4. Apply database migrations

python manage.py makemigrations
python manage.py migrate


5. Create a superuser (for admin access)

python manage.py createsuperuser


6. (Optional) Seed test data or create test users

python setup_test_data.py
python create_admin.py
python create_browser_test_users.py


7. Run the development server

python manage.py runserver
# then open http://127.0.0.1:8000/ in your browser




---

✅ Running tests

The project includes multiple tests under tests/. You can run:

# With pytest
pytest -q

# Or with Django’s test runner
python manage.py test


---

⚙️ Useful management scripts

create_admin.py — create admin accounts / bootstrap users

create_browser_test_users.py — create sample users for browser-based testing

setup_test_data.py — seed database with sample clients, accounts and transactions

reproduce_error.py, reproduce_issue.py — helper scripts for reproducing/debugging issues


Run them with the virtual environment active:

python create_admin.py
python setup_test_data.py


---

🛡 Security & best practices (notes)

Use environment variables for sensitive settings (e.g. SECRET_KEY, database credentials).

Pin dependencies in requirements.txt and update regularly.

For production: collect static files, and run with a WSGI server (e.g. Gunicorn / uWSGI) + HTTPS via proxy (nginx, etc.).



---

🧩 Contributing

1. Fork the repo.


2. Create a feature branch: git checkout -b feature/your-feature.


3. Commit your changes and submit a Pull Request.


4. Make sure tests pass before requesting review.




---

📚 Documentation & Staff test flows

See STAFF_MANUAL_TEST.md for staff workflow and test instructions.


---

📄 License

This project is open-source; add a LICENSE file if desired for license terms.

---


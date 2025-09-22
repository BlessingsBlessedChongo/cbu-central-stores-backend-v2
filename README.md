# CBU Central Stores Management System V2

A blockchain-based inventory management system for Copperbelt University Central Stores.

## 🚀 Features

- **Blockchain Integration**: All critical operations logged on Ethereum blockchain
- **Role-Based Access Control**: Admin, Stores Manager, Procurement, CFO, Department Dean
- **Multi-Level Approval Workflow**: Sequential approval process with audit trail
- **Real-time Notifications**: WebSocket-based live notifications
- **Stock Management**: Complete inventory tracking with low stock alerts
- **Delivery & Damage Tracking**: Comprehensive goods management
- **RESTful API**: Fully documented API endpoints

## 🛠️ Technology Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Blockchain**: Solidity 0.8.x + Web3.py + Ganache
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Real-time**: Django Channels + Redis
- **Authentication**: JWT Tokens
- **Documentation**: Swagger/OpenAPI
- **Task Queue**: Celery + Redis

## 📋 Prerequisites

### Windows 11 Development Environment
1. **Python 3.11+**: [Download from python.org](https://python.org)
2. **Node.js** (for Ganache): [Download from nodejs.org](https://nodejs.org)
3. **Git**: [Download from git-scm.com](https://git-scm.com)
4. **VSCode**: [Download from code.visualstudio.com](https://code.visualstudio.com)
5. **Redis**: [Download for Windows](https://github.com/microsoftarchive/redis/releases)

### VSCode Extensions
- Python
- Django
- Solidity
- Thunder Client (API testing)
- Docker (optional)

## 🏗️ Installation & Setup

### 1. Clone and Setup Project
```bash
git clone https://github.com/your-username/cbu-central-stores-backend-v2.git
cd cbu-central-stores-backend-v2

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
2. Environment Configuration
bash
# Copy environment template
cp .env.example .env

# Edit .env file with your values
# Required variables:
# DEBUG=True
# SECRET_KEY=your-super-secret-key
# WEB3_PROVIDER_URI=http://127.0.0.1:7545
# DEPLOYER_ACCOUNT_ADDRESS=0xYourGanacheAccount
# DEPLOYER_PRIVATE_KEY=YourGanachePrivateKey
# FERNET_KEY=your-fernet-encryption-key
# REDIS_URL=redis://127.0.0.1:6379/0
```
### 3. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
4. Blockchain Setup
bash
# Install Ganache CLI
npm install -g ganache-cli

# Start Ganache (in separate terminal)
ganache-cli -p 7545 -h 0.0.0.0 --deterministic

# Compile and deploy contract
python manage.py compile_contract
python manage.py deploy_contract
5. Start Development Servers
bash
# Terminal 1 - Django development server
python manage.py runserver 0.0.0.0:8000

# Terminal 2 - Redis server
redis-server

# Terminal 3 - Celery worker
celery -A central_stores worker --loglevel=info

# Terminal 4 - Celery beat (for scheduled tasks)
celery -A central_stores beat --loglevel=info
📚 API Documentation
Once the server is running, access the API documentation:

Swagger UI: http://0.0.0.0:8000/swagger/

ReDoc: http://0.0.0.0:8000/redoc/

API Overview: http://0.0.0.0:8000/

🧪 Testing
Run Tests
bash
# Run all tests
pytest

# Run specific test module
pytest core/tests/test_authentication.py -v

# Run with coverage
pytest --cov=core --cov-report=html
Postman Collection
Import CBU_Central_Stores.postman_collection.json into Postman

Set up environment variables in Postman:

base_url: http://0.0.0.0:8000

admin_token: JWT token from admin login

user_token: JWT token from user login
```
### 🔧 Management Commands
```bash
# Blockchain operations
python manage.py compile_contract
python manage.py deploy_contract
python manage.py start_event_listener

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Utility commands
python manage.py check_low_stock
python manage.py send_approval_reminders
python manage.py cleanup_old_notifications
```
### 🚀 Deployment
Production Deployment Checklist
Environment Setup

```bash
# Set production environment variables
export DEBUG=False
export DJANGO_SETTINGS_MODULE=central_stores.settings.production
export DB_NAME=your_production_db
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
```
### Database Migration

```bash
python manage.py migrate
python manage.py collectstatic
Gunicorn Setup


pip install gunicorn
gunicorn central_stores.asgi:application -k uvicorn.workers.UvicornWorker
Nginx Configuration

nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/your/staticfiles/;
    }
}
```
### SSL Certificate (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com
🔒 Security Considerations
Private Key Encryption: All blockchain private keys are encrypted using Fernet

JWT Authentication: Secure token-based authentication with short expiration

CORS Configuration: Properly configured Cross-Origin Resource Sharing

HTTPS Enforcement: SSL redirect in production environment

Password Validation: Strong password requirements enforced

SQL Injection Protection: Django ORM prevents SQL injection

XSS Protection: Built-in Django XSS protection
```
### 📊 Monitoring & Logging
Log Files
Django errors: logs/django-error.log

Application logs: logs/app.log

Blockchain events: logs/blockchain.log

Health Checks
bash
# API health check
curl http://0.0.0.0:8000/api/blockchain/status/

# Database health check
python manage.py check --database default

# Celery health check
celery -A central_stores inspect ping
### 🤝 Contributing
Fork the repository
```
Create feature branch: git checkout -b feature/amazing-feature

Commit changes: git commit -m 'Add amazing feature'

Push to branch: git push origin feature/amazing-feature
```
Open a Pull Request

### 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

### 🆘 Support
For support and questions:

Email: stores@cbu.edu.zm

Issues: GitHub Issues

Documentation: API Docs

### 🔄 Version History
v2.0.0 - Complete blockchain integration, multi-level approval, real-time notifications

v1.0.0 - Initial release with basic CRUD functionality

Made with ❤️ for Copperbelt University


# Growing Grubs Setup Guide

This guide covers how to set up and run the Growing Grubs application in different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Docker Setup](#docker-setup)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Git
- (Optional) Docker and Docker Compose for containerized setup

### Python Version Check

```bash
python --version
# Should output: Python 3.11.x or higher
```

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Growing-Grubs.git
cd Growing-Grubs
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Key variables to configure:**

- `SECRET_KEY`: Generate a secure key (see below)
- `WTF_CSRF_SECRET_KEY`: Another secure key for CSRF protection
- `DATABASE_URL`: Database connection string
- `NHS_API_KEY`: Your NHS API key (get from https://api.service.nhs.uk/)

**Generating Secure Keys:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize the Database

```bash
# Run database migrations
flask db upgrade

# Or, if using Flask-Migrate directly:
flask migrate
```

### 6. Run the Application

```bash
# Development mode (with auto-reload and debug toolbar)
python server_main.py

# Application will be available at http://localhost:10000
```

## Environment Configuration

### Configuration Files

- `.env.example`: Template for environment variables
- `.env`: Your local environment configuration (created from .env.example)
- `mod/config.py`: Application configuration classes
- `mod/env_loader.py`: Environment variable loader utilities

### Environment Variables

All configurable environment variables are documented in `.env.example`. Key sections include:

#### Flask Configuration
- `FLASK_ENV`: Environment mode (development, production, testing)
- `SECRET_KEY`: Flask session secret key (IMPORTANT: change in production)
- `WTF_CSRF_SECRET_KEY`: CSRF protection secret key

#### Database
- `DATABASE_URL`: Database connection string
  - Development: `sqlite:///./mod/database.db`
  - Production: `postgresql://user:password@host/dbname`

#### External APIs
- `NHS_API_KEY`: Health topics API key
- `NUTRITIONIX_API_KEY`: Nutritional information API key (optional)

#### Logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE`: Path to application log file
- `ERROR_LOG_FILE`: Path to error log file

#### Security
- `SESSION_COOKIE_SECURE`: Use secure cookies (True in production)
- `SESSION_COOKIE_HTTPONLY`: HttpOnly flag for cookies
- `SESSION_COOKIE_SAMESITE`: SameSite policy (Strict, Lax, None)

### Configuration Classes

The application has three built-in configuration classes:

#### DevelopmentConfig
- Debug mode enabled
- SQL query echoing enabled
- Suitable for local development

#### ProductionConfig
- Debug mode disabled
- SQL query echoing disabled
- Secure cookie settings enforced
- Suitable for production deployment

#### TestingConfig
- In-memory SQLite database
- CSRF protection disabled
- Suitable for automated testing

## Docker Setup

### Building the Docker Image

```bash
# Build the Docker image
docker build -t growing-grubs:latest .

# Or with docker-compose
docker-compose build
```

### Running with Docker Compose

#### Development Mode

```bash
# Start all services
docker-compose up

# In detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

#### With PostgreSQL (Production-like)

```bash
# Start with database profile
docker-compose --profile dev up

# This will start web, db, and redis services
```

### Docker Compose Services

- **web**: Flask application (port 10000)
- **db**: PostgreSQL database (optional, port 5432)
- **redis**: Redis cache (optional, port 6379)

### Accessing the Application

After starting Docker Compose, the application is available at:
```
http://localhost:10000
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Generate strong `SECRET_KEY` and `WTF_CSRF_SECRET_KEY`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Configure production database (`DATABASE_URL`)
- [ ] Obtain API keys for external services
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `SESSION_COOKIE_SAMESITE=Strict`
- [ ] Configure logging to appropriate locations
- [ ] Set up SSL/TLS certificates
- [ ] Configure backups for database

### Environment Setup for Production

```bash
# Copy and configure .env for production
cp .env.example .env.production

# Configure with production values
# Key differences from development:
# - FLASK_ENV=production
# - DEBUG=False
# - SQLALCHEMY_ECHO=False
# - SESSION_COOKIE_SECURE=True
# - DATABASE_URL=postgresql://...
# - Real API keys
```

### Using Docker in Production

```bash
# Build for production
docker build -t growing-grubs:1.0.0 .

# Run with production configuration
docker run \
  --env-file .env.production \
  -e FLASK_ENV=production \
  -e DEBUG=False \
  --restart unless-stopped \
  --name growing-grubs \
  -p 10000:10000 \
  growing-grubs:1.0.0
```

### Using Application Server (Gunicorn)

For production, use a proper application server instead of Flask's development server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:10000 server_main:application

# With more configuration
gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 0.0.0.0:10000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  server_main:application
```

### Reverse Proxy Setup (Nginx)

Example Nginx configuration for reverse proxy:

```nginx
upstream growing_grubs {
    server localhost:10000;
}

server {
    listen 80;
    server_name example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://growing_grubs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Common Issues

#### 1. "No module named 'mod'"

**Cause**: Python path not set correctly

**Solution**:
```bash
# Ensure you're running from the project root
cd /path/to/Growing-Grubs

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/Growing-Grubs"
```

#### 2. "Database is locked"

**Cause**: SQLite database is being accessed by multiple processes

**Solution**:
- Ensure only one Flask instance is running
- Close any other connections to the database
- Consider using PostgreSQL for production

#### 3. "NHS_API_KEY is missing"

**Cause**: Environment variable not set

**Solution**:
```bash
# Set the variable
export NHS_API_KEY="your-api-key-here"

# Or add to .env file
echo "NHS_API_KEY=your-api-key-here" >> .env
```

#### 4. "Port 10000 already in use"

**Cause**: Another process is using port 10000

**Solution**:
```bash
# Find process using port 10000
lsof -i :10000

# Kill the process (replace PID with actual process ID)
kill -9 PID

# Or use a different port
PORT=10001 python server_main.py
```

#### 5. "CSRF validation failed"

**Cause**: CSRF token mismatch or expired session

**Solution**:
- Clear browser cookies and session data
- Ensure `WTF_CSRF_SECRET_KEY` is consistent
- Check session configuration in `.env`

### Debugging Tips

#### Enable Debug Logging

```bash
# In .env, set:
LOG_LEVEL=DEBUG
DEBUG=True
SQLALCHEMY_ECHO=True
```

#### View Application Logs

```bash
# View recent logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log

# Search for errors
grep ERROR logs/app.log
```

#### Database Inspection

```bash
# Open SQLite database shell
sqlite3 mod/database.db

# List tables
.tables

# Query data
SELECT * FROM users;
```

#### Flask Shell

```bash
# Open interactive Flask shell
flask shell

# Now you can interact with the application:
from mod.models import Users, Recipe
users = Users.query.all()
print(len(users))
```

## Next Steps

1. **Customize Configuration**: Edit `.env` with your specific needs
2. **Configure API Keys**: Get and set up external API keys
3. **Set Up Database**: Run migrations and seed initial data
4. **Test the Application**: Visit http://localhost:10000
5. **Read Documentation**: Check other docs in `/docs` directory

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [NHS API Documentation](https://api.service.nhs.uk/)

## Support

For issues or questions, refer to:
- Project README: `README.md`
- Technical Documentation: `docs/technical-documentation.md`
- Process Documentation: `docs/process-documentation.md`

# Production Deployment Guide for IOAgent

## Environment Variables Setup

### 1. Generate Secure Keys

**CRITICAL**: Never use the example keys in production. Generate strong random keys:

```bash
# Generate SECRET_KEY
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Generate JWT_SECRET_KEY  
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Set environment
export FLASK_ENV=production

# Set your domain for CORS
export PROD_CORS_ORIGINS=https://yourdomain.com
```

### 2. Environment Variable Validation

The application will **fail to start** in production if these are not set:
- `SECRET_KEY` - Flask session security
- `JWT_SECRET_KEY` - JWT token signing
- `FLASK_ENV=production` - Enables production mode

### 3. Current Environment Variables

You provided:
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here        # ⚠️  CHANGE THIS
export JWT_SECRET_KEY=your-jwt-secret-key-here # ⚠️  CHANGE THIS  
export PROD_CORS_ORIGINS=https://yourdomain.com # ✅ Update domain
```

## Quick Setup Commands

### For Development
```bash
export FLASK_ENV=development
export SECRET_KEY=dev-key-only
export JWT_SECRET_KEY=dev-jwt-key-only
export DEV_CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### For Production
```bash
# 1. Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Set environment variables
export FLASK_ENV=production
export SECRET_KEY="$SECRET_KEY"
export JWT_SECRET_KEY="$JWT_SECRET_KEY"
export PROD_CORS_ORIGINS=https://your-actual-domain.com

# 3. Verify they're set
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:10}..."
echo "FLASK_ENV: $FLASK_ENV"
echo "CORS_ORIGINS: $PROD_CORS_ORIGINS"
```

## Deployment Checklist

### ✅ Before Deployment
- [ ] Generate and set secure SECRET_KEY
- [ ] Generate and set secure JWT_SECRET_KEY  
- [ ] Set FLASK_ENV=production
- [ ] Update PROD_CORS_ORIGINS with your domain
- [ ] Install dependencies: `pip install -r IOAgent-backend/requirements.txt`
- [ ] Run database migrations
- [ ] Test authentication endpoints

### ✅ Security Verification
```bash
# Test that production mode is active
python3 -c "
import os
print('FLASK_ENV:', os.environ.get('FLASK_ENV'))
print('SECRET_KEY set:', bool(os.environ.get('SECRET_KEY')))
print('JWT_SECRET_KEY set:', bool(os.environ.get('JWT_SECRET_KEY')))
"
```

### ✅ Database Setup
```bash
# Initialize database with migrations
export FLASK_APP=IOAgent-backend.app
python3 -m flask db init
python3 -m flask db migrate -m "Initial production migration"
python3 -m flask db upgrade
```

### ✅ Create Initial Admin User
```python
from IOAgent_backend.app import app
from src.models.user import db, User
import getpass

with app.app_context():
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = getpass.getpass("Admin password: ")
    
    admin = User(username=username, email=email, role='admin')
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user '{username}' created successfully!")
```

## Platform-Specific Deployment

### Heroku
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY="your-generated-secret-key"
heroku config:set JWT_SECRET_KEY="your-generated-jwt-key"
heroku config:set PROD_CORS_ORIGINS="https://yourapp.herokuapp.com"
```

### Docker
```dockerfile
ENV FLASK_ENV=production
ENV SECRET_KEY=your-generated-secret-key
ENV JWT_SECRET_KEY=your-generated-jwt-key
ENV PROD_CORS_ORIGINS=https://yourdomain.com
```

### Render/Railway/Vercel
Set environment variables in your platform's dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY=your-generated-secret-key`
- `JWT_SECRET_KEY=your-generated-jwt-key`
- `PROD_CORS_ORIGINS=https://yourdomain.com`

## Security Features Enabled in Production

When `FLASK_ENV=production`:
- ✅ Secure JWT token validation
- ✅ HTTPS-only session cookies
- ✅ Strict CORS policy
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ Error message sanitization
- ✅ Required secret key validation

## Testing Production Setup

### 1. Test Application Startup
```bash
cd /path/to/IOAgent
python3 IOAgent-backend/app.py
```

Should see:
```
INFO - Starting application on port 5000 (debug=False)
INFO - CORS origins configured: ['https://yourdomain.com']
INFO - Database initialized
```

### 2. Test Authentication API
```bash
# Register a test user
curl -X POST https://yourdomain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser", 
    "email": "test@example.com",
    "password": "SecurePass123"
  }'

# Login to get token
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

### 3. Test Protected Endpoints
```bash
# This should fail (401 Unauthorized)
curl https://yourdomain.com/api/projects

# This should succeed with valid token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://yourdomain.com/api/projects
```

## Monitoring and Maintenance

### Log Analysis
Monitor these in production:
- Authentication failures
- Invalid token attempts  
- CORS violations
- Database connection issues

### Health Check
The app includes a health endpoint:
```bash
curl https://yourdomain.com/api/health
```

### Backup Strategy
- Regular database backups
- Environment variable backups
- Application code versioning

## Troubleshooting

### Common Issues

1. **"SECRET_KEY must be set in production"**
   - Solution: Set environment variable before starting app

2. **"JWT_SECRET_KEY must be set in production"**
   - Solution: Set JWT secret key environment variable

3. **CORS errors in browser**
   - Solution: Verify PROD_CORS_ORIGINS matches your domain exactly

4. **Authentication not working**
   - Check JWT_SECRET_KEY is consistent across restarts
   - Verify tokens aren't expired (24-hour limit)

The application is now ready for production deployment with enterprise-grade security! 🚀
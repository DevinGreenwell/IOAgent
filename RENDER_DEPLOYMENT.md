# Render.com Deployment Guide for IOAgent

## 🚀 Quick Setup for https://ioagent.onrender.com

### 1. Set Environment Variables in Render Dashboard

Go to your Render service settings and add these environment variables:

```
FLASK_ENV=production
SECRET_KEY=bFecBfKDmkpK0k0qoxcpugXS7aSfRxJUbGUCSyt3Yz0
JWT_SECRET_KEY=BlXZXyhPV-C8VRuaaLp7BEjKF8sX4c9lhsLJGFbpq0o
PROD_CORS_ORIGINS=https://ioagent.onrender.com
```

### 2. Render Build and Start Commands

**Build Command:**
```bash
pip install -r IOAgent-backend/requirements.txt
```

**Start Command:**
```bash
cd IOAgent-backend && python app.py
```

### 3. Database Initialization

Add this to your build command or run once after deployment:

```bash
pip install -r IOAgent-backend/requirements.txt && \
export FLASK_APP=IOAgent-backend.app && \
python -m flask db init && \
python -m flask db migrate -m "Initial production migration" && \
python -m flask db upgrade
```

### 4. Create Admin User (Run once after first deployment)

Create a script `create_admin.py`:

```python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from IOAgent_backend.app import app
from src.models.user import db, User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        if User.query.filter_by(username='admin').first():
            print("Admin user already exists")
            return
        
        admin = User(
            username='admin',
            email='admin@ioagent.onrender.com',
            role='admin'
        )
        admin.set_password('AdminPass123!')  # Change this password!
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: AdminPass123!")
        print("⚠️  CHANGE THE PASSWORD IMMEDIATELY AFTER LOGIN!")

if __name__ == "__main__":
    create_admin()
```

Run it once: `python create_admin.py`

### 5. Test Your Deployment

#### Test Health Check
```bash
curl https://ioagent.onrender.com/api/health
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2025-01-XX..."
}
```

#### Test Registration
```bash
curl -X POST https://ioagent.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "SecurePass123"
  }'
```

#### Test Login
```bash
curl -X POST https://ioagent.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

#### Test Protected Endpoint
```bash
# Should return 401 without token
curl https://ioagent.onrender.com/api/projects

# Should work with valid token
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://ioagent.onrender.com/api/projects
```

## 🔧 Render-Specific Configuration

### Dockerfile (Optional - if using Docker)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r IOAgent-backend/requirements.txt

ENV FLASK_ENV=production
ENV PORT=10000

EXPOSE 10000

CMD ["python", "IOAgent-backend/app.py"]
```

### render.yaml (Infrastructure as Code)
```yaml
services:
  - type: web
    name: ioagent
    env: python
    buildCommand: pip install -r IOAgent-backend/requirements.txt
    startCommand: cd IOAgent-backend && python app.py
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        value: bFecBfKDmkpK0k0qoxcpugXS7aSfRxJUbGUCSyt3Yz0
      - key: JWT_SECRET_KEY
        value: BlXZXyhPV-C8VRuaaLp7BEjKF8sX4c9lhsLJGFbpq0o
      - key: PROD_CORS_ORIGINS
        value: https://ioagent.onrender.com
```

## 🛡️ Security Checklist for Production

- ✅ Secure keys generated and set
- ✅ HTTPS enforced (automatic on Render)
- ✅ CORS configured for your domain
- ✅ Authentication required on all endpoints
- ✅ Production environment variables set
- ✅ Database migrations ready
- ⚠️ Change default admin password immediately
- ⚠️ Set up regular database backups
- ⚠️ Monitor application logs

## 📊 Monitoring Your Deployment

### Application Logs
Monitor in Render dashboard for:
- Authentication attempts
- Database connections
- Error messages
- Performance metrics

### Key Metrics to Watch
- Response times
- Authentication success/failure rates
- Database query performance
- Memory and CPU usage

Your IOAgent application is now ready for production deployment on Render! 🎉

## Next Steps

1. **Deploy**: Push changes and deploy on Render
2. **Test**: Verify all endpoints work correctly
3. **Create Users**: Set up initial admin and test users
4. **Monitor**: Watch logs and performance
5. **Scale**: Upgrade Render plan as needed

The authentication system will ensure your application is secure and production-ready!
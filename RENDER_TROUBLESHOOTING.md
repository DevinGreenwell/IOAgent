# 🔧 Render Deployment Troubleshooting for IOAgent

## ❌ Current Error: Flask-Migrate==5.1.0 version not found

### Root Cause
Flask-Migrate 5.1.0 doesn't exist. The latest version is 4.1.0. The requirements.txt has been updated.

## ✅ IMMEDIATE FIX

### Option 1: Update Your Render Service Settings

In your Render dashboard, update these settings:

**Build Command:**
```bash
pip install -r IOAgent-backend/requirements.txt
```

**Start Command:**
```bash
cd IOAgent-backend && python app.py
```

**Environment Variables:**
```
FLASK_ENV=production
SECRET_KEY=bFecBfKDmkpK0k0qoxcpugXS7aSfRxJUbGUCSyt3Yz0
JWT_SECRET_KEY=BlXZXyhPV-C8VRuaaLp7BEjKF8sX4c9lhsLJGFbpq0o
PROD_CORS_ORIGINS=https://ioagent.onrender.com
PYTHON_VERSION=3.11.0
```

### Option 2: Alternative Build Command

If Option 1 doesn't work, try this build command:

```bash
cd IOAgent-backend && pip install -r requirements.txt
```

### Option 3: Use Minimal Requirements

For faster deployment with only essential packages:

```bash
pip install -r requirements-minimal.txt
```

### Option 4: Fixed Requirements

The issue was Flask-Migrate==5.1.0 doesn't exist. Use:

```bash
pip install -r IOAgent-backend/requirements.txt
```

(Now fixed with Flask-Migrate==4.1.0)

## 🔍 Debug Steps

### 1. Check Build Logs
Look for these in your Render build logs:
```
Successfully installed Flask-JWT-Extended-4.6.0
```

### 2. Verify Python Path
Add this to your start command for debugging:
```bash
cd IOAgent-backend && python -c "import sys; print(sys.path)" && python app.py
```

### 3. Test Requirements Installation
Temporarily use this build command to debug:
```bash
pip install -r IOAgent-backend/requirements.txt && python -c "import flask_jwt_extended; print('JWT Extension imported successfully')"
```

## 🚀 Step-by-Step Fix Instructions

### 1. In Render Dashboard

1. Go to your IOAgent service
2. Click **Settings**
3. Update **Build Command** to:
   ```
   pip install -r IOAgent-backend/requirements.txt
   ```
4. Update **Start Command** to:
   ```
   cd IOAgent-backend && python app.py
   ```
5. Click **Manual Deploy** to trigger new deployment

### 2. Monitor Build Logs

Watch for:
- ✅ `Successfully installed Flask-JWT-Extended-4.6.0`
- ✅ `Successfully installed bcrypt-4.2.1`
- ✅ `Build successful 🎉`

### 3. If Still Failing

Try this alternative approach in Render settings:

**Build Command:**
```bash
python -m pip install --upgrade pip && pip install -r IOAgent-backend/requirements.txt
```

**Start Command:**
```bash
cd IOAgent-backend && python -m flask --app app run --host=0.0.0.0 --port=$PORT
```

## 🛠️ Alternative: Use requirements.txt at Root

If the path issue persists, we can move requirements.txt to the root:

### Create Root Requirements File

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
cd IOAgent-backend && python app.py
```

## 📋 Quick Checklist

- [ ] Build command: `pip install -r IOAgent-backend/requirements.txt`
- [ ] Start command: `cd IOAgent-backend && python app.py`
- [ ] Python version: 3.11.0
- [ ] All environment variables set
- [ ] Requirements.txt includes Flask-JWT-Extended==4.6.0
- [ ] Build logs show successful installation

## 🔄 After Making Changes

1. **Manual Deploy**: Trigger in Render dashboard
2. **Monitor Logs**: Watch build and deployment logs
3. **Test Endpoint**: `curl https://ioagent.onrender.com/api/health`

## 💡 Most Likely Solution

Update your Render service with:

**Build Command:**
```
pip install -r IOAgent-backend/requirements.txt
```

**Start Command:**
```
cd IOAgent-backend && python app.py
```

Then trigger a manual deploy. This should resolve the ModuleNotFoundError.

## 🆘 If All Else Fails

Use this comprehensive build command:

```bash
pip install --upgrade pip && \
pip install Flask==3.1.1 Flask-JWT-Extended==4.6.0 Flask-CORS==6.0.0 Flask-SQLAlchemy==3.1.1 Flask-Migrate==5.1.0 bcrypt==4.2.1 && \
pip install -r IOAgent-backend/requirements.txt
```

This explicitly installs the critical packages first, then installs the rest.
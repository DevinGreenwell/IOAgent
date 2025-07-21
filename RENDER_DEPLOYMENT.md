# Render Deployment Guide for IOAgent

This guide will help you deploy IOAgent to Render with a PostgreSQL database for persistent data storage.

## Prerequisites

1. A Render account (https://render.com)
2. A GitHub repository with the IOAgent code

## Step 1: Create a PostgreSQL Database on Render

1. Log in to your Render dashboard
2. Click "New +" → "PostgreSQL"
3. Configure your database:
   - **Name**: `ioagent-db` (or your preferred name)
   - **Database**: Leave as default
   - **User**: Leave as default
   - **Region**: Choose the same region you'll use for your web service
   - **PostgreSQL Version**: 15 or later
   - **Plan**: Free tier is sufficient for testing
4. Click "Create Database"
5. Wait for the database to be created (this may take a few minutes)
6. Once created, copy the **Internal Database URL** (it will look like `postgresql://username:password@hostname/database_name`)

## Step 2: Create a Web Service on Render

1. From your Render dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure your web service:
   - **Name**: `ioagent` (or your preferred name)
   - **Region**: Same as your database
   - **Branch**: `master` (or your default branch)
   - **Root Directory**: Leave empty
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free tier for testing

## Step 3: Configure Environment Variables

In your web service settings, go to the "Environment" tab and add these variables:

### Required Variables:

1. **DATABASE_URL**
   - Value: The Internal Database URL from your PostgreSQL database
   - Example: `postgresql://user:password@dpg-xxxxx.oregon-postgres.render.com/ioagent_db`

2. **SECRET_KEY**
   - Value: A secure random string (at least 32 characters)
   - Generate one: `python -c "import secrets; print(secrets.token_hex(32))"`

3. **JWT_SECRET_KEY**
   - Value: Another secure random string (different from SECRET_KEY)
   - Generate one: `python -c "import secrets; print(secrets.token_hex(32))"`

4. **FLASK_ENV**
   - Value: `production`

5. **ANTHROPIC_API_KEY** (Optional - for AI features)
   - Value: Your Anthropic API key from https://console.anthropic.com/
   - Note: The app will work without this, but AI features will be disabled

### Optional Variables:

6. **PORT** (Render sets this automatically)
   - Render will provide this, don't set it manually

7. **CORS_ORIGINS** (if you have a custom frontend domain)
   - Value: Your frontend URL (e.g., `https://myapp.com`)

## Step 4: Deploy

1. Click "Manual Deploy" → "Deploy latest commit"
2. Watch the deployment logs for any errors
3. Once deployed, click on your service URL to test

## Step 5: Initialize the Database

After your first deployment, you need to create the database tables:

1. In your Render web service, go to the "Shell" tab
2. Run these commands:
   ```bash
   python
   from app import app, db
   with app.app_context():
       db.create_all()
       print("Database tables created successfully!")
   exit()
   ```

## Step 6: Test Registration

1. Visit your deployed app URL
2. Try to register a new account
3. The registration should now persist even after service restarts

## Troubleshooting

### Registration not working?

1. **Check logs**: Go to your web service → Logs tab
2. **Verify DATABASE_URL**: Ensure it's set correctly in environment variables
3. **Check CORS**: If using a separate frontend, ensure CORS origins are configured
4. **Database connection**: Verify the database is running and accessible

### Common Issues:

1. **"SECRET_KEY must be set in production"**
   - Make sure you've set both SECRET_KEY and JWT_SECRET_KEY environment variables

2. **Database connection errors**
   - Verify your DATABASE_URL is correct
   - Ensure your database and web service are in the same region
   - Check that the database is active

3. **CORS errors**
   - The app is configured to allow requests from standard Render URLs
   - If using a custom domain, update the CORS configuration in `app.py`

4. **Import errors for psycopg2**
   - Make sure `requirements.txt` includes `psycopg2-binary>=2.9.5`
   - The build logs should show psycopg2 being installed

## Security Notes

1. **Never commit secrets**: Keep your SECRET_KEY, JWT_SECRET_KEY, and API keys in environment variables only
2. **Use HTTPS**: Render provides HTTPS by default
3. **Database security**: Use the internal database URL for better security
4. **Regular updates**: Keep your dependencies updated for security patches

## Next Steps

1. Set up a custom domain (optional)
2. Configure email services for password reset (if needed)
3. Set up monitoring and alerts
4. Consider upgrading to paid tiers for production use

## Support

If you encounter issues:
1. Check the Render documentation: https://render.com/docs
2. Review application logs in the Render dashboard
3. Ensure all environment variables are set correctly
4. Verify database connectivity
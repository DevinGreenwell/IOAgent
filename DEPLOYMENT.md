# IOAgent GitHub Pages Deployment Setup

## Overview
This document outlines the setup for deploying IOAgent to GitHub Pages. Since GitHub Pages only supports static sites, we'll create a hybrid approach where the frontend can be deployed statically while the backend runs separately.

## Deployment Strategy

### Option 1: Static Frontend Only (Recommended for GitHub Pages)
- Deploy the frontend as a static site on GitHub Pages
- Backend runs on a separate server (Heroku, Railway, etc.)
- Frontend communicates with backend via API calls

### Option 2: Full Static Build (Alternative)
- Convert the Flask app to generate static files
- Pre-build all possible pages and data
- Limited functionality but fully static

## GitHub Pages Setup Files

### 1. GitHub Actions Workflow
Create `.github/workflows/deploy.yml` for automatic deployment.

### 2. Build Script
Create a build script that prepares the static files for deployment.

### 3. Configuration Files
- `package.json` for Node.js dependencies (if needed)
- `_config.yml` for Jekyll configuration
- `.nojekyll` to bypass Jekyll processing

## Implementation

### Static Frontend Deployment
The frontend (HTML, CSS, JS) can be deployed directly to GitHub Pages with the backend API URL configured to point to a hosted backend service.

### Backend Hosting Options
1. **Heroku** - Easy deployment with git integration
2. **Railway** - Modern platform with automatic deployments
3. **PythonAnywhere** - Python-focused hosting
4. **DigitalOcean App Platform** - Scalable container hosting

## Environment Variables for Production
- `OPENAI_API_KEY` - Set in backend hosting environment
- `API_BASE_URL` - Frontend configuration for backend location
- `FLASK_ENV` - Set to 'production'

## Build Process
1. Copy static files (HTML, CSS, JS) to deployment directory
2. Update API endpoints to point to production backend
3. Optimize assets (minify CSS/JS)
4. Deploy to GitHub Pages

## CORS Configuration
Backend must be configured to accept requests from the GitHub Pages domain:
- `https://[username].github.io`
- Custom domain if configured

## Security Considerations
- API keys stored securely in backend environment
- CORS properly configured
- Rate limiting on API endpoints
- Input validation and sanitization


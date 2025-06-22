# IOAgent - Required Fixes Implementation Guide

## 1. Security Fix - render.yaml

**CRITICAL**: Remove hardcoded secrets immediately!

```yaml
services:
  - type: web
    name: ioagent
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r IOAgent-backend/requirements.txt
    startCommand: cd IOAgent-backend && python app.py
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true  # Let Render generate this
      - key: JWT_SECRET_KEY
        generateValue: true  # Let Render generate this
      - key: PROD_CORS_ORIGINS
        value: https://ioagent.onrender.com
      - key: PYTHON_VERSION
        value: 3.11.0
```

## 2. Frontend Authentication Fix

In `IOAgent-backend/app.js`, update the `makeAuthenticatedRequest` method:

```javascript
async makeAuthenticatedRequest(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Always add Authorization header if token exists
    if (this.accessToken) {
        headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle 401 responses
        if (response.status === 401) {
            // Token expired or invalid
            this.logout();
            throw new Error('Authentication required');
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}
```

## 3. Fix API Calls

Update all API calls to use `makeAuthenticatedRequest`:

```javascript
async loadDashboard() {
    try {
        const response = await this.makeAuthenticatedRequest(`${this.apiBase}/projects`);
        const data = await response.json();

        if (data.success) {
            this.displayProjects(data.projects);
            this.updateDashboardStats(data.projects);
        } else {
            throw new Error(data.error || 'Failed to load projects');
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        if (error.message !== 'Authentication required') {
            this.showAlert('Error loading projects: ' + error.message, 'danger');
        }
    }
}
```

## 4. Fix Button Event Handlers

Replace inline onclick handlers in HTML with proper event delegation:

```javascript
setupButtonListeners() {
    // Use event delegation for dynamically created elements
    document.addEventListener('click', (e) => {
        // Project card clicks
        if (e.target.closest('.project-card')) {
            const projectId = e.target.closest('.project-card').dataset.projectId;
            if (projectId) this.openProject(projectId);
        }
        
        // Delete evidence button
        if (e.target.closest('.btn-delete-evidence')) {
            const evidenceId = e.target.closest('.btn-delete-evidence').dataset.evidenceId;
            if (evidenceId) this.deleteEvidence(evidenceId);
        }
        
        // Edit timeline button
        if (e.target.closest('.btn-edit-timeline')) {
            const entryId = e.target.closest('.btn-edit-timeline').dataset.entryId;
            if (entryId) this.editTimelineEntry(entryId);
        }
        
        // Delete timeline button
        if (e.target.closest('.btn-delete-timeline')) {
            const entryId = e.target.closest('.btn-delete-timeline').dataset.entryId;
            if (entryId) this.deleteTimelineEntry(entryId);
        }
    });
}
```

## 5. Fix Project Data Structure

Update the API to return data in the expected format:

```python
# In api.py, update the to_dict methods:

def project_to_dict(project):
    return {
        'id': project.id,
        'metadata': {
            'title': project.title,
            'investigating_officer': project.investigating_officer,
            'status': project.status,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        },
        'incident_info': {
            'incident_date': project.incident_date.isoformat() if project.incident_date else None,
            'location': project.incident_location,
            'incident_type': project.incident_type
        },
        'evidence_library': [e.to_dict() for e in project.evidence],
        'timeline': [t.to_dict() for t in project.timeline_entries],
        'causal_factors': [c.to_dict() for c in project.causal_factors]
    }
```

## 6. Fix CORS for Production

Update CORS configuration in `IOAgent-backend/app.py`:

```python
def get_cors_origins():
    """Get CORS origins based on environment"""
    if os.environ.get('FLASK_ENV') == 'production':
        # Allow the actual production domain
        return ['https://ioagent.onrender.com']
    else:
        # Development origins
        return [
            'http://localhost:3000',
            'http://127.0.0.1:5000',
            'http://localhost:5000'
        ]
```

## 7. Fix Loading Overlay

Add this CSS to ensure loading overlay displays properly:

```css
#loadingOverlay {
    position: fixed !important;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    display: none;
    justify-content: center;
    align-items: center;
}

#loadingOverlay[style*="display: flex"] {
    display: flex !important;
}
```

## Testing Steps

1. **Test Authentication**:
   - Register new user
   - Login with credentials
   - Verify token is included in API calls

2. **Test Project Management**:
   - Create new project
   - Update project information
   - Verify data saves correctly

3. **Test File Upload**:
   - Upload various file types
   - Verify file size limits
   - Check file appears in evidence list

4. **Test Timeline**:
   - Add timeline entries
   - Edit existing entries
   - Delete entries

5. **Test Analysis**:
   - Run causal analysis
   - Verify results display
   - Test ROI generation

## Deployment Checklist

- [ ] Update render.yaml with environment variables
- [ ] Deploy updated backend code
- [ ] Clear browser cache
- [ ] Test all features in production
- [ ] Monitor error logs
- [ ] Verify CORS working correctly
# IOAgent Architecture Implementation Plan

## Priority 1: Critical Security and Stability Issues (Week 1)

### 1.1 Fix Production Database
**Current Issue**: Using SQLite in production
```python
# Create src/config/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseConfig:
    @staticmethod
    def get_database_url():
        if os.environ.get('FLASK_ENV') == 'production':
            # Use PostgreSQL in production
            return os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
        # Use SQLite for development
        return 'sqlite:///./src/database/dev.db'
    
    @staticmethod
    def create_engine():
        url = DatabaseConfig.get_database_url()
        if 'postgresql' in url:
            return create_engine(url, pool_size=10, max_overflow=20)
        return create_engine(url)
```

### 1.2 Implement Proper Security Headers and CORS
```python
# Create src/security/middleware.py
from flask import Flask
import os

class SecurityMiddleware:
    @staticmethod
    def init_app(app: Flask):
        @app.after_request
        def add_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            if os.environ.get('FLASK_ENV') == 'production':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                # Restrict CORS properly
                response.headers['Access-Control-Allow-Origin'] = 'https://ioagent.onrender.com'
            
            return response
```

### 1.3 Add Rate Limiting
```python
# requirements.txt addition
flask-limiter==3.5.0

# Create src/security/rate_limiter.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

# Apply to routes
@limiter.limit("5 per minute")
@api_bp.route('/projects', methods=['POST'])
def create_project():
    pass
```

## Priority 2: Code Organization (Week 2)

### 2.1 Split app.py into Modules

```python
# src/config/app_config.py
import os
from datetime import timedelta

class Config:
    # Base configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../../uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DEBUG = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # Production specific initialization

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

```python
# src/app_factory.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from src.config.app_config import config
from src.models.user import db
from src.routes import register_blueprints
from src.security.middleware import SecurityMiddleware

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    JWTManager(app)
    Migrate(app, db)
    CORS(app)
    
    # Security
    SecurityMiddleware.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app
```

### 2.2 Create Utility Modules

```python
# src/utils/file_handler.py
import os
from werkzeug.utils import secure_filename
from typing import Optional, Tuple

class FileHandler:
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx',
        'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mp3', 'wav'
    }
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_file(file, project_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        if not file or not FileHandler.allowed_file(file.filename):
            return False, None, "Invalid file type"
        
        filename = secure_filename(file.filename)
        # Additional implementation
        return True, filepath, None
```

## Priority 3: Service Layer Implementation (Week 3)

### 3.1 Create Service Layer

```python
# src/services/project_service.py
from typing import List, Optional
from src.models.user import Project, db
from src.utils.exceptions import ValidationError, NotFoundError

class ProjectService:
    def __init__(self):
        self.db = db
    
    def create_project(self, title: str, officer: str, user_id: int) -> Project:
        """Create a new project with validation"""
        if not title or len(title) < 3:
            raise ValidationError("Project title must be at least 3 characters")
        
        project = Project(
            title=title[:200],
            investigating_officer=officer[:100] if officer else None,
            user_id=user_id,
            status='draft'
        )
        
        self.db.session.add(project)
        self.db.session.commit()
        return project
    
    def get_project(self, project_id: str, user_id: int) -> Project:
        """Get project with authorization check"""
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            raise NotFoundError(f"Project {project_id} not found")
        
        # Add authorization check
        if project.user_id != user_id:
            raise ValidationError("Unauthorized access to project")
        
        return project
    
    def update_project(self, project_id: str, user_id: int, **kwargs) -> Project:
        """Update project with validation"""
        project = self.get_project(project_id, user_id)
        
        # Update allowed fields
        allowed_fields = ['title', 'investigating_officer', 'status', 
                         'incident_date', 'incident_location', 'incident_type']
        
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(project, field, value)
        
        self.db.session.commit()
        return project
```

### 3.2 Refactor Routes to Use Services

```python
# src/routes/api.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.project_service import ProjectService
from src.utils.exceptions import ValidationError, NotFoundError

api_bp = Blueprint('api', __name__)
project_service = ProjectService()

@api_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        project = project_service.create_project(
            title=data.get('title', ''),
            officer=data.get('investigating_officer', ''),
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'project': project.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error creating project: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
```

## Priority 4: Testing Infrastructure (Week 4)

### 4.1 Set Up Testing Framework

```python
# requirements-dev.txt
pytest==7.4.0
pytest-cov==4.1.0
pytest-flask==1.2.0
pytest-mock==3.11.1
factory-boy==3.3.0

# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=html --cov-report=term-missing
```

### 4.2 Create Test Fixtures

```python
# tests/conftest.py
import pytest
from src.app_factory import create_app
from src.models.user import db, User

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Create test user and get JWT token
    user = User(username='testuser', email='test@example.com')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()
    
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}
```

### 4.3 Write Unit Tests

```python
# tests/unit/test_project_service.py
import pytest
from src.services.project_service import ProjectService
from src.utils.exceptions import ValidationError

class TestProjectService:
    def test_create_project_success(self, app):
        service = ProjectService()
        project = service.create_project(
            title="Test Project",
            officer="Test Officer",
            user_id=1
        )
        assert project.title == "Test Project"
        assert project.status == "draft"
    
    def test_create_project_invalid_title(self, app):
        service = ProjectService()
        with pytest.raises(ValidationError):
            service.create_project(title="", officer="Test", user_id=1)
```

## Priority 5: Frontend Modernization (Weeks 5-6)

### 5.1 Create React Frontend Structure

```bash
# Create new frontend
npx create-react-app frontend --template typescript
cd frontend
npm install axios react-router-dom @types/react-router-dom zustand
```

### 5.2 Implement State Management

```typescript
// frontend/src/store/projectStore.ts
import { create } from 'zustand';
import axios from 'axios';

interface Project {
  id: string;
  title: string;
  status: string;
  // ... other fields
}

interface ProjectStore {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  
  fetchProjects: () => Promise<void>;
  createProject: (data: Partial<Project>) => Promise<void>;
  selectProject: (id: string) => void;
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,
  
  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const response = await axios.get('/api/projects');
      set({ projects: response.data.projects, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
  
  createProject: async (data) => {
    // Implementation
  },
  
  selectProject: (id) => {
    const project = get().projects.find(p => p.id === id);
    set({ currentProject: project });
  }
}));
```

## Monitoring and Maintenance

### Setup Logging and Monitoring

```python
# src/utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/ioagent.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('IOAgent startup')
```

### Add Health Checks

```python
# src/routes/health.py
from flask import Blueprint, jsonify
from src.models.user import db
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    health_status = {
        'status': 'healthy',
        'database': 'unknown',
        'version': os.environ.get('APP_VERSION', '1.0.0')
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health_status['database'] = 'connected'
    except:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
    
    return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
```

## Success Metrics

1. **Code Quality**:
   - Test coverage > 80%
   - Cyclomatic complexity < 10
   - No security vulnerabilities

2. **Performance**:
   - API response time < 200ms
   - Page load time < 3s
   - Database query time < 100ms

3. **Reliability**:
   - Uptime > 99.9%
   - Error rate < 0.1%
   - Zero data loss incidents

4. **Maintainability**:
   - Deployment time < 10 minutes
   - New feature development time reduced by 50%
   - Onboarding time for new developers < 1 week
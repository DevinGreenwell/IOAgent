# IOAgent - Marine Casualty Investigation System

IOAgent is a comprehensive web application designed for the U.S. Coast Guard to streamline marine casualty investigations. It provides tools for evidence management, timeline construction, causal analysis using the Swiss Cheese model, and automated Report of Investigation (ROI) generation.

## Features

- 📁 **Project Management**: Create and manage investigation projects
- 📄 **Evidence Management**: Upload and organize investigation documents
- 📅 **Timeline Builder**: Create chronological event sequences
- 🧀 **Swiss Cheese Model**: Analyze causal factors systematically
- 🤖 **AI-Powered Analysis**: Generate insights using Claude AI
- 📊 **ROI Generation**: Automated report creation
- 🔐 **Secure Authentication**: JWT-based user authentication
- 🚀 **Async Processing**: Background tasks for heavy operations
- 💾 **Caching**: Redis-based caching for performance

## Tech Stack

### Backend
- Python 3.8+
- Flask (Web Framework)
- SQLAlchemy (ORM)
- PostgreSQL/SQLite (Database)
- Celery (Async Tasks)
- Redis (Caching & Message Broker)
- JWT (Authentication)

### Frontend
- React 18
- TypeScript
- Material-UI
- Redux Toolkit
- React Query
- React Router

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis (optional, for full features)
- PostgreSQL (optional, SQLite works for development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/DevinGreenwell/IOAgent.git
cd IOAgent
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

3. Run the application:

**Option A: Full Stack (Recommended)**
```bash
./run_full_stack.sh
```

**Option B: Backend only**
```bash
./run_backend_only.sh
```

**Option C: Frontend only**
```bash
./run_frontend_only.sh
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

## Development

### Backend Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with hot reload
python app.py
```

### Frontend Development
```bash
cd frontend
npm install --legacy-peer-deps
npm start
```

### Running Tests
```bash
# Backend tests
./run_tests.sh

# Frontend tests
cd frontend && npm test
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

## Project Structure

```
IOAgent/
├── frontend/              # React TypeScript frontend
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   ├── store/        # Redux store
│   │   └── types/        # TypeScript types
├── src/                   # Flask backend
│   ├── config/           # Configuration
│   ├── models/           # Database models
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   ├── tasks/            # Celery tasks
│   └── utils/            # Utilities
├── tests/                 # Test files
├── docs/                  # Documentation
└── docker-compose.yml     # Docker configuration
```

## API Documentation

The API follows RESTful conventions:

- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/:id` - Get project details
- `POST /api/evidence/upload` - Upload evidence
- `POST /api/projects/:id/timeline` - Add timeline entry
- `POST /api/projects/:id/generate-roi` - Generate ROI

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- All API endpoints require authentication (except auth endpoints)
- Input validation and sanitization on all user inputs
- Rate limiting to prevent abuse
- Environment variables for sensitive configuration
- CSRF protection enabled

## License

This project is proprietary software for the U.S. Coast Guard.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team

## Acknowledgments

- U.S. Coast Guard for project requirements
- Anthropic Claude AI for analysis capabilities
- Open source community for excellent tools and libraries
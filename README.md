# IOAgent - USCG Report of Investigation Generator

A Python-based web application that generates perfectly formatted USCG Reports of Investigation (ROI) from user-provided information, with upload functionality and AI assistance.

## Features

- **Project-based Workspace**: Each investigation is its own work environment
- **File Upload & Processing**: Support for PDF, DOCX, images, videos, and audio files
- **Timeline Builder**: Create chronological entries for Actions, Conditions, and Events
- **Causal Analysis**: Automated analysis using USCG methodology and Swiss Cheese model
- **AI Integration**: OpenAI-powered suggestions and content improvement
- **ROI Generation**: Automatically generate properly formatted ROI documents
- **Evidence Management**: Link evidence to timeline entries and analysis

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ioagent
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_ENV=development
   ```

5. **Run the application**
   ```bash
   cd src
   python main.py
   ```

6. **Access the application**
   Open your browser and go to `http://localhost:5000`

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI assistance features
- `FLASK_ENV`: Set to 'development' for local development, 'production' for deployment

## Application Structure

```
ioagent/
├── src/
│   ├── models/
│   │   ├── roi_models.py          # Data models for ROI components
│   │   ├── roi_generator.py       # ROI document generation logic
│   │   ├── ai_assistant.py        # AI integration for suggestions
│   │   └── project_manager.py     # Project and file management
│   ├── routes/
│   │   ├── api.py                 # API endpoints
│   │   └── user.py                # User management (template)
│   ├── static/
│   │   ├── index.html             # Main application interface
│   │   └── app.js                 # Frontend JavaScript
│   └── main.py                    # Flask application entry point
├── projects/                      # Project data storage
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Usage Guide

### 1. Create a New Investigation
- Click "New Investigation" on the dashboard
- Enter investigation title and investigating officer name
- The project workspace will open automatically

### 2. Set Up Project Information
- Navigate to "Project Info" tab
- Fill in incident details (date, location, type, etc.)
- Save the project information

### 3. Upload Evidence
- Go to "Evidence" tab
- Drag and drop files or click to upload
- Supported formats: PDF, DOCX, images, videos, audio
- AI will automatically analyze uploaded documents for timeline suggestions

### 4. Build Timeline
- Navigate to "Timeline" tab
- Add entries for Actions, Conditions, and Events
- Link evidence to timeline entries
- Mark the initiating event

### 5. Perform Causal Analysis
- Go to "Analysis" tab
- Click "Run Analysis" to identify causal factors
- AI will suggest factors based on timeline and evidence
- Review and refine the analysis

### 6. Generate ROI Document
- Navigate to "ROI Generator" tab
- Check readiness status
- Click "Generate ROI" to create the document
- Download the generated DOCX file

## ROI Document Structure

The generated ROI follows USCG standards and includes:

1. **Executive Summary**
   - Scene setting paragraph
   - Outcomes paragraph
   - Causal factors paragraph

2. **Investigating Officer's Report**
   - Preliminary Statement
   - Vessels Involved
   - Record of Casualties (if applicable)
   - Findings of Fact
   - Analysis
   - Conclusions
   - Actions Taken (if applicable)
   - Recommendations (if applicable)

## Causal Analysis Methodology

The application implements the USCG Swiss Cheese model with five factor categories:

- **Organization**: Management decisions, policies, culture
- **Workplace**: Physical environment, equipment, procedures
- **Precondition**: Individual factors, team factors, environmental factors
- **Production**: Unsafe acts, errors, violations
- **Defense**: Barriers that failed or were absent

## AI Features

When an OpenAI API key is provided, the application offers:

- **Timeline Suggestions**: Automatically suggest timeline entries from uploaded documents
- **Causal Factor Identification**: AI-powered analysis of contributing factors
- **Content Improvement**: Enhance analysis text for clarity and professionalism
- **Executive Summary Generation**: Automatically generate summary paragraphs
- **Consistency Checking**: Identify inconsistencies across ROI sections

## Deployment

### GitHub Pages (Static Frontend)

1. **Build static files**
   ```bash
   python build_static.py
   ```

2. **Deploy to GitHub Pages**
   - Push to main branch
   - GitHub Actions will automatically deploy
   - Configure backend URL in `build_static.py`

### Backend Hosting

The Flask backend can be deployed to:
- Heroku
- Railway
- PythonAnywhere
- DigitalOcean App Platform

See `DEPLOYMENT.md` for detailed deployment instructions.

## API Endpoints

- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `POST /api/projects/{id}/upload` - Upload file
- `POST /api/projects/{id}/timeline` - Add timeline entry
- `POST /api/projects/{id}/causal-analysis` - Run causal analysis
- `POST /api/projects/{id}/generate-roi` - Generate ROI document

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is developed for the U.S. Coast Guard and is intended for official use in marine casualty investigations.

## Support

For technical support or questions about ROI methodology, please contact the development team or refer to the USCG Marine Investigations Documentation and Reporting Procedures Manual.

## Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive configuration
- Ensure proper CORS configuration for production deployment
- Validate all user inputs and uploaded files


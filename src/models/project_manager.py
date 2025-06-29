# Project management and file processing utilities

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
import magic
import PyPDF2
from docx import Document as DocxDocument

from src.models.roi_models import InvestigationProject, Evidence, TimelineEntry
from src.models.anthropic_assistant import AnthropicAssistant

class ProjectManager:
    """Manages investigation projects and file operations"""
    
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
        self.ai_assistant = AnthropicAssistant()
        self._ensure_projects_dir()
    
    def _ensure_projects_dir(self):
        """Ensure projects directory exists"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
    
    def create_project(self, title: str, investigating_officer: str = "") -> InvestigationProject:
        """Create a new investigation project"""
        project = InvestigationProject()
        project.metadata.title = title
        project.metadata.investigating_officer = investigating_officer
        
        # Create project directory
        project_dir = self._get_project_dir(project.id)
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "exports"), exist_ok=True)
        
        # Save project
        self.save_project(project)
        return project
    
    def load_project(self, project_id: str) -> Optional[InvestigationProject]:
        """Load an existing project"""
        project_file = os.path.join(self._get_project_dir(project_id), "project.json")
        if not os.path.exists(project_file):
            return None
        
        try:
            project = InvestigationProject()
            project.load_from_file(project_file)
            return project
        except Exception as e:
            print(f"Error loading project {project_id}: {e}")
            return None
    
    def save_project(self, project: InvestigationProject):
        """Save project to disk"""
        project_dir = self._get_project_dir(project.id)
        project_file = os.path.join(project_dir, "project.json")
        project.metadata.updated_at = datetime.now()
        project.save_to_file(project_file)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with metadata"""
        projects = []
        
        for item in os.listdir(self.projects_dir):
            project_dir = os.path.join(self.projects_dir, item)
            if os.path.isdir(project_dir):
                project_file = os.path.join(project_dir, "project.json")
                if os.path.exists(project_file):
                    try:
                        with open(project_file, 'r') as f:
                            data = json.load(f)
                            projects.append({
                                'id': data.get('id', item),
                                'title': data.get('metadata', {}).get('title', 'Untitled'),
                                'status': data.get('metadata', {}).get('status', 'draft'),
                                'created_at': data.get('metadata', {}).get('created_at', ''),
                                'updated_at': data.get('metadata', {}).get('updated_at', '')
                            })
                    except Exception as e:
                        print(f"Error reading project metadata for {item}: {e}")
        
        # Sort by updated_at descending
        projects.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return projects
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its files"""
        project_dir = self._get_project_dir(project_id)
        if os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
                return True
            except Exception as e:
                print(f"Error deleting project {project_id}: {e}")
                return False
        return False
    
    def upload_file(self, project_id: str, file, description: str = "") -> Dict[str, Any]:
        """Upload and process a file for a project, returning timeline suggestions"""
        if not file or not file.filename:
            return {"success": False, "error": "No file provided"}
        
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return {"success": False, "error": "Invalid filename"}
        
        # Save file to uploads directory
        uploads_dir = os.path.join(self._get_project_dir(project_id), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        
        # Handle duplicate filenames
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        try:
            file.save(file_path)
        except Exception as e:
            print(f"Error saving file: {e}")
            return {"success": False, "error": f"Failed to save file: {str(e)}"}
        
        # Process file content to extract timeline entries
        timeline_suggestions = []
        content = self._extract_file_content(file_path)
        if content:
            # Use AI to suggest timeline entries
            project = self.load_project(project_id)
            if project:
                timeline_suggestions = self.ai_assistant.suggest_timeline_entries(content, project.timeline)
        
        return {
            "success": True,
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_type": self._determine_file_type(file_path),
            "timeline_suggestions": timeline_suggestions,
            "message": f"File uploaded successfully. Found {len(timeline_suggestions)} potential timeline entries."
        }
    
    def _get_project_dir(self, project_id: str) -> str:
        """Get project directory path"""
        return os.path.join(self.projects_dir, project_id)
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type from file"""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            
            if mime_type.startswith('image/'):
                return 'photo'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
            elif mime_type in ['application/pdf', 'application/msword', 
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return 'document'
            elif mime_type.startswith('text/'):
                return 'document'
            else:
                return 'document'  # Default to document
        except:
            # Fallback to extension-based detection for documents only
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx']:
                return 'document'
            else:
                return 'document'  # Default to document for any other file type
    
    def _extract_file_content(self, file_path: str) -> Optional[str]:
        """Extract text content from file"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                return self._extract_pdf_content(file_path)
            elif ext in ['.docx']:
                return self._extract_docx_content(file_path)
            elif ext in ['.txt', '.md']:
                return self._extract_text_content(file_path)
            else:
                return None
        except Exception as e:
            print(f"Error extracting content from {file_path}: {e}")
            return None
    
    def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return ""
    
    def _extract_docx_content(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting DOCX content: {e}")
            return ""
    
    def _extract_text_content(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting text content: {e}")
            return ""

class TimelineBuilder:
    """Utilities for building and managing timeline"""
    
    def __init__(self):
        self.ai_assistant = AnthropicAssistant()
    
    def add_entry(self, project: InvestigationProject, entry_data: Dict[str, Any]) -> TimelineEntry:
        """Add a new timeline entry"""
        entry = TimelineEntry()
        entry.timestamp = datetime.fromisoformat(entry_data.get('timestamp', ''))
        entry.type = entry_data.get('type', 'action')
        entry.description = entry_data.get('description', '')
        entry.personnel_involved = entry_data.get('personnel_involved', [])
        entry.evidence_ids = entry_data.get('evidence_ids', [])
        entry.assumptions = entry_data.get('assumptions', [])
        entry.confidence_level = entry_data.get('confidence_level', 'high')
        entry.is_initiating_event = entry_data.get('is_initiating_event', False)
        
        project.timeline.append(entry)
        return entry
    
    def sort_timeline(self, project: InvestigationProject):
        """Sort timeline entries by timestamp"""
        project.timeline.sort(key=lambda x: x.timestamp or datetime.min)
    
    def validate_timeline(self, project: InvestigationProject) -> List[Dict[str, str]]:
        """Validate timeline for completeness and consistency"""
        issues = []
        
        # Check for missing timestamps
        for entry in project.timeline:
            if not entry.timestamp:
                issues.append({
                    'type': 'warning',
                    'entry_id': entry.id,
                    'message': 'Timeline entry missing timestamp'
                })
        
        # Check for evidence support
        for entry in project.timeline:
            if not entry.evidence_ids:
                issues.append({
                    'type': 'warning',
                    'entry_id': entry.id,
                    'message': 'Timeline entry has no supporting evidence'
                })
        
        # Check for initiating event
        initiating_events = [e for e in project.timeline if e.is_initiating_event]
        if not initiating_events:
            issues.append({
                'type': 'error',
                'entry_id': '',
                'message': 'No initiating event identified'
            })
        elif len(initiating_events) > 1:
            issues.append({
                'type': 'warning',
                'entry_id': '',
                'message': 'Multiple initiating events identified'
            })
        
        return issues


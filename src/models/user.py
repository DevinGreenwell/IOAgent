from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # user, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set the user's password"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(100), primary_key=True)  # UUID string
    title = db.Column(db.String(200), nullable=False)
    investigating_officer = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')  # draft, in_progress, complete
    incident_date = db.Column(db.DateTime)
    incident_location = db.Column(db.Text)
    incident_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for now
    
    # Relationships
    evidence_items = db.relationship('Evidence', backref='project', lazy=True, cascade='all, delete-orphan')
    timeline_entries = db.relationship('TimelineEntry', backref='project', lazy=True, cascade='all, delete-orphan')
    causal_factors = db.relationship('CausalFactor', backref='project', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.title}>'

    def to_dict(self, include_relationships=True):
        data = {
            'id': self.id,
            'title': self.title,
            'investigating_officer': self.investigating_officer,
            'status': self.status,
            'incident_date': self.incident_date.isoformat() if self.incident_date else None,
            'incident_location': self.incident_location,
            'incident_type': self.incident_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }
        
        if include_relationships:
            data.update({
                'evidence_library': [item.to_dict(include_project=False) for item in self.evidence_items],
                'timeline': [entry.to_dict(include_project=False) for entry in self.timeline_entries],
                'causal_factors': [factor.to_dict(include_project=False) for factor in self.causal_factors],
                'metadata': {
                    'title': self.title,
                    'investigating_officer': self.investigating_officer,
                    'status': self.status
                },
                'incident_info': {
                    'incident_date': self.incident_date.isoformat() if self.incident_date else None,
                    'location': self.incident_location,
                    'incident_type': self.incident_type
                }
            })
        
        return data

class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    id = db.Column(db.String(100), primary_key=True)  # UUID string
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Relative path to file
    file_size = db.Column(db.Integer)  # File size in bytes
    mime_type = db.Column(db.String(100))
    file_type = db.Column(db.String(50))  # document, photo, video, audio, etc.
    description = db.Column(db.Text)
    source = db.Column(db.String(100), default='user_upload')
    reliability = db.Column(db.String(20), default='high')  # high, medium, low
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    project_id = db.Column(db.String(100), db.ForeignKey('projects.id'), nullable=False)
    
    # Relationships
    timeline_refs = db.relationship('TimelineEntry', secondary='timeline_evidence', back_populates='evidence_items')

    def __repr__(self):
        return f'<Evidence {self.filename}>'

    def to_dict(self, include_project=True):
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'type': self.file_type,
            'description': self.description,
            'source': self.source,
            'reliability': self.reliability,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'timeline_refs': [entry.id for entry in self.timeline_refs]
        }
        
        if include_project:
            data['project_id'] = self.project_id
            
        return data

class TimelineEntry(db.Model):
    __tablename__ = 'timeline_entries'
    
    id = db.Column(db.String(100), primary_key=True)  # UUID string
    timestamp = db.Column(db.DateTime, nullable=False)
    entry_type = db.Column(db.String(50), nullable=False)  # action, observation, communication, etc.
    description = db.Column(db.Text, nullable=False)
    personnel_involved = db.Column(db.Text)  # JSON array of personnel
    assumptions = db.Column(db.Text)  # JSON array of assumptions
    confidence_level = db.Column(db.String(20), default='medium')  # high, medium, low
    is_initiating_event = db.Column(db.Boolean, default=False)
    analysis_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    project_id = db.Column(db.String(100), db.ForeignKey('projects.id'), nullable=False)
    
    # Relationships
    evidence_items = db.relationship('Evidence', secondary='timeline_evidence', back_populates='timeline_refs')

    def __repr__(self):
        return f'<TimelineEntry {self.entry_type} at {self.timestamp}>'

    @property
    def personnel_involved_list(self):
        """Get personnel_involved as a list"""
        if self.personnel_involved:
            try:
                return json.loads(self.personnel_involved)
            except:
                return []
        return []

    @personnel_involved_list.setter
    def personnel_involved_list(self, value):
        """Set personnel_involved from a list"""
        self.personnel_involved = json.dumps(value) if value else None

    @property
    def assumptions_list(self):
        """Get assumptions as a list"""
        if self.assumptions:
            try:
                return json.loads(self.assumptions)
            except:
                return []
        return []

    @assumptions_list.setter
    def assumptions_list(self, value):
        """Set assumptions from a list"""
        self.assumptions = json.dumps(value) if value else None

    def to_dict(self, include_project=True):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'type': self.entry_type,
            'description': self.description,
            'personnel_involved': self.personnel_involved_list,
            'assumptions': self.assumptions_list,
            'confidence_level': self.confidence_level,
            'is_initiating_event': self.is_initiating_event,
            'analysis_notes': self.analysis_notes,
            'evidence_ids': [evidence.id for evidence in self.evidence_items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_project:
            data['project_id'] = self.project_id
            
        return data

class CausalFactor(db.Model):
    __tablename__ = 'causal_factors'
    
    id = db.Column(db.String(100), primary_key=True)  # UUID string
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # human, technical, organizational, environmental
    severity = db.Column(db.String(20), default='medium')  # high, medium, low
    likelihood = db.Column(db.String(20), default='medium')  # high, medium, low
    analysis_text = db.Column(db.Text)
    recommendations = db.Column(db.Text)  # JSON array of recommendations
    evidence_support = db.Column(db.Text)  # JSON array of evidence IDs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key
    project_id = db.Column(db.String(100), db.ForeignKey('projects.id'), nullable=False)

    def __repr__(self):
        return f'<CausalFactor {self.title}>'

    @property
    def recommendations_list(self):
        """Get recommendations as a list"""
        if self.recommendations:
            try:
                return json.loads(self.recommendations)
            except:
                return []
        return []

    @recommendations_list.setter
    def recommendations_list(self, value):
        """Set recommendations from a list"""
        self.recommendations = json.dumps(value) if value else None

    @property
    def evidence_support_list(self):
        """Get evidence_support as a list"""
        if self.evidence_support:
            try:
                return json.loads(self.evidence_support)
            except:
                return []
        return []

    @evidence_support_list.setter
    def evidence_support_list(self, value):
        """Set evidence_support from a list"""
        self.evidence_support = json.dumps(value) if value else None

    def to_dict(self, include_project=True):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'severity': self.severity,
            'likelihood': self.likelihood,
            'analysis_text': self.analysis_text,
            'recommendations': self.recommendations_list,
            'evidence_support': self.evidence_support_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_project:
            data['project_id'] = self.project_id
            
        return data

# Association table for many-to-many relationship between timeline entries and evidence
timeline_evidence = db.Table('timeline_evidence',
    db.Column('timeline_id', db.String(100), db.ForeignKey('timeline_entries.id'), primary_key=True),
    db.Column('evidence_id', db.String(100), db.ForeignKey('evidence.id'), primary_key=True)
)

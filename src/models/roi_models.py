# Core data models for IOAgent ROI generation

from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import uuid

class BaseModel:
    """Base model with common functionality"""
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, BaseModel):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [item.to_dict() if isinstance(item, BaseModel) else item for item in value]
            else:
                result[key] = value
        return result
    
    def from_dict(self, data: Dict[str, Any]):
        """Load model from dictionary"""
        for key, value in data.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                setattr(self, key, datetime.fromisoformat(value))
            else:
                setattr(self, key, value)

class ProjectMetadata(BaseModel):
    """Project metadata and configuration"""
    def __init__(self):
        super().__init__()
        self.title = ""
        self.investigating_officer = ""
        self.status = "draft"  # draft, review, complete
        self.description = ""

class IncidentInfo(BaseModel):
    """Basic incident information"""
    def __init__(self):
        super().__init__()
        self.incident_date = None
        self.location = ""
        self.incident_type = ""  # collision, allision, fire, etc.
        self.weather_conditions = {}
        self.casualties_summary = ""

class Vessel(BaseModel):
    """Vessel information model"""
    def __init__(self):
        super().__init__()
        self.official_name = ""
        self.identification_number = ""
        self.flag = ""
        self.vessel_class = ""
        self.vessel_type = ""
        self.vessel_subtype = ""
        self.build_year = None
        self.gross_tonnage = None
        self.length = None
        self.beam = None
        self.draft = None
        self.propulsion = ""

class Personnel(BaseModel):
    """Personnel involved in incident"""
    def __init__(self):
        super().__init__()
        self.role = ""  # Captain, Crewmember, Passenger, etc.
        self.vessel_assignment = ""
        self.credentials = []
        self.experience = ""
        self.status = ""  # injured, deceased, uninjured

class Evidence(BaseModel):
    """Evidence item model"""
    def __init__(self):
        super().__init__()
        self.type = ""  # document, photo, video, audio, witness_statement, physical
        self.filename = ""
        self.description = ""
        self.source = ""
        self.reliability = "high"  # high, medium, low
        self.timeline_refs = []  # Timeline entry IDs this evidence supports
        self.file_path = ""

class TimelineEntry(BaseModel):
    """Timeline entry model"""
    def __init__(self):
        super().__init__()
        self.timestamp = None
        self.type = ""  # action, condition, event
        self.description = ""
        self.personnel_involved = []
        self.evidence_ids = []
        self.assumptions = []
        self.confidence_level = "high"  # high, medium, low
        self.is_initiating_event = False

class CausalFactor(BaseModel):
    """Causal factor model"""
    def __init__(self):
        super().__init__()
        self.event_id = ""  # Timeline entry ID this factor relates to
        self.category = ""  # organization, workplace, precondition, production, defense
        self.subcategory = ""
        self.title = ""
        self.description = ""
        self.evidence_support = []  # Evidence IDs supporting this factor
        self.analysis_text = ""

class Finding(BaseModel):
    """Finding of fact model"""
    def __init__(self):
        super().__init__()
        self.statement = ""
        self.evidence_support = []  # Evidence IDs
        self.timeline_refs = []  # Timeline entry IDs
        self.analysis_refs = []  # Analysis section IDs that reference this

class AnalysisSection(BaseModel):
    """Analysis section model"""
    def __init__(self):
        super().__init__()
        self.title = ""
        self.finding_refs = []  # Finding IDs that support this analysis
        self.causal_factor_id = ""
        self.analysis_text = ""
        self.conclusion_refs = []  # Conclusion IDs that derive from this

class Conclusion(BaseModel):
    """Conclusion model"""
    def __init__(self):
        super().__init__()
        self.statement = ""
        self.analysis_refs = []  # Analysis section IDs that support this
        self.causal_factor_refs = []  # Direct causal factor references

class ExecutiveSummary(BaseModel):
    """Executive summary model"""
    def __init__(self):
        super().__init__()
        self.title = ""  # Auto-generated
        self.scene_setting = ""  # Paragraph 1
        self.outcomes = ""  # Paragraph 2
        self.causal_factors = ""  # Paragraph 3

class ROIDocument(BaseModel):
    """Complete ROI document model"""
    def __init__(self):
        super().__init__()
        self.executive_summary = ExecutiveSummary()
        self.preliminary_statement = ""
        self.vessels_involved = []
        self.casualties = []
        self.findings_of_fact = []
        self.analysis_sections = []
        self.conclusions = []
        self.actions_taken = ""
        self.recommendations = ""

class InvestigationProject(BaseModel):
    """Main project container"""
    def __init__(self):
        super().__init__()
        self.metadata = ProjectMetadata()
        self.incident_info = IncidentInfo()
        self.vessels = []
        self.personnel = []
        self.timeline = []
        self.evidence_library = []
        self.causal_factors = []
        self.roi_document = ROIDocument()
    
    def save_to_file(self, filepath: str):
        """Save project to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load project from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.from_dict(data)


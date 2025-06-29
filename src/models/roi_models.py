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
        """Load model from dictionary with proper object reconstruction"""
        for key, value in data.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                setattr(self, key, datetime.fromisoformat(value))
            elif isinstance(value, dict) and hasattr(self, key):
                # Handle nested objects
                current_attr = getattr(self, key)
                if isinstance(current_attr, BaseModel):
                    current_attr.from_dict(value)
            elif isinstance(value, list) and hasattr(self, key):
                # Handle lists of objects
                current_attr = getattr(self, key, None)
                if current_attr is not None and len(current_attr) > 0 and isinstance(current_attr[0], BaseModel):
                    # Reconstruct list of model objects
                    obj_type = type(current_attr[0])
                    new_list = []
                    for item in value:
                        if isinstance(item, dict):
                            new_obj = obj_type()
                            new_obj.from_dict(item)
                            new_list.append(new_obj)
                        else:
                            new_list.append(item)
                    setattr(self, key, new_list)
                else:
                    # Handle empty lists or lists of simple types
                    setattr(self, key, value)
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
        self.location_detail = ""      # e.g. "near Warren Channel, AK"
        self.time_zone = ""            # Olson tz name, e.g. "America/Juneau"
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
        self.owner = ""
        self.owner_location = ""
        self.operator = ""
        self.operator_location = ""

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
    
    def from_dict(self, data: Dict[str, Any]):
        """Custom from_dict for ROIDocument with proper nested object handling"""
        # Handle basic fields
        super().from_dict(data)
        
        # Handle nested ExecutiveSummary
        if 'executive_summary' in data and isinstance(data['executive_summary'], dict):
            self.executive_summary.from_dict(data['executive_summary'])

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
    
    def from_dict(self, data: Dict[str, Any]):
        """Custom from_dict for InvestigationProject with proper nested object handling"""
        # Handle basic fields first
        for key, value in data.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                setattr(self, key, datetime.fromisoformat(value))
            elif key in ['id']:
                setattr(self, key, value)
        
        # Handle nested objects explicitly
        if 'metadata' in data and isinstance(data['metadata'], dict):
            self.metadata.from_dict(data['metadata'])
        
        if 'incident_info' in data and isinstance(data['incident_info'], dict):
            self.incident_info.from_dict(data['incident_info'])
        
        if 'roi_document' in data and isinstance(data['roi_document'], dict):
            self.roi_document.from_dict(data['roi_document'])
        
        # Handle lists with proper object reconstruction
        if 'timeline' in data and isinstance(data['timeline'], list):
            self.timeline = []
            for item in data['timeline']:
                if isinstance(item, dict):
                    entry = TimelineEntry()
                    entry.from_dict(item)
                    self.timeline.append(entry)
        
        if 'evidence_library' in data and isinstance(data['evidence_library'], list):
            self.evidence_library = []
            for item in data['evidence_library']:
                if isinstance(item, dict):
                    evidence = Evidence()
                    evidence.from_dict(item)
                    self.evidence_library.append(evidence)
        
        if 'causal_factors' in data and isinstance(data['causal_factors'], list):
            self.causal_factors = []
            for item in data['causal_factors']:
                if isinstance(item, dict):
                    factor = CausalFactor()
                    factor.from_dict(item)
                    self.causal_factors.append(factor)
        
        # Handle other simple lists
        for key in ['vessels', 'personnel']:
            if key in data:
                setattr(self, key, data[key])


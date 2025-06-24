# ROI Converter - Transform database models to ROI models for document generation

from datetime import datetime
from typing import List, Dict, Any, Optional
import os

from src.models.roi_models import (
    InvestigationProject, ProjectMetadata, IncidentInfo, Vessel, Personnel,
    Evidence, TimelineEntry, CausalFactor, Finding, AnalysisSection, 
    Conclusion, ExecutiveSummary, ROIDocument
)

class DatabaseToROIConverter:
    """Converts SQLAlchemy database models to ROI models for document generation"""
    
    def __init__(self):
        pass
    
    def convert_project(self, db_project) -> InvestigationProject:
        """Convert a database Project to InvestigationProject"""
        roi_project = InvestigationProject()
        
        # Convert basic metadata
        roi_project.metadata = self._convert_metadata(db_project)
        
        # Convert incident information
        roi_project.incident_info = self._convert_incident_info(db_project)
        
        # Convert timeline entries
        roi_project.timeline = self._convert_timeline_entries(db_project.timeline_entries)
        
        # Convert evidence items
        roi_project.evidence_library = self._convert_evidence_items(db_project.evidence_items)
        
        # Convert causal factors
        roi_project.causal_factors = self._convert_causal_factors(db_project.causal_factors)
        
        # For now, create empty vessels and personnel (can be enhanced later)
        roi_project.vessels = self._create_default_vessels(db_project)
        roi_project.personnel = self._create_default_personnel(db_project)
        
        # Generate ROI document structure
        roi_project.roi_document = self._generate_roi_document(roi_project)
        
        return roi_project
    
    def _convert_metadata(self, db_project) -> ProjectMetadata:
        """Convert database project to ProjectMetadata"""
        metadata = ProjectMetadata()
        metadata.title = db_project.title or "Investigation Report"
        metadata.investigating_officer = db_project.investigating_officer or "Unknown"
        metadata.status = db_project.status or "draft"
        metadata.description = f"Investigation of {db_project.incident_type or 'incident'} on {db_project.incident_date.strftime('%B %d, %Y') if db_project.incident_date else 'unknown date'}"
        return metadata
    
    def _convert_incident_info(self, db_project) -> IncidentInfo:
        """Convert database project to IncidentInfo"""
        incident_info = IncidentInfo()
        incident_info.incident_date = db_project.incident_date
        incident_info.location = db_project.incident_location or "Unknown location"
        incident_info.incident_type = db_project.incident_type or "Unknown incident type"
        incident_info.weather_conditions = {}  # Could be enhanced with weather data
        incident_info.casualties_summary = "Casualties to be determined"  # Could be enhanced
        return incident_info
    
    def _convert_timeline_entries(self, db_timeline_entries) -> List[TimelineEntry]:
        """Convert database timeline entries to ROI TimelineEntry objects"""
        timeline = []
        
        for db_entry in db_timeline_entries:
            roi_entry = TimelineEntry()
            roi_entry.id = db_entry.id
            roi_entry.timestamp = db_entry.timestamp
            roi_entry.type = db_entry.entry_type
            roi_entry.description = db_entry.description
            roi_entry.personnel_involved = db_entry.personnel_involved_list or []
            roi_entry.evidence_ids = [evidence.id for evidence in db_entry.evidence_items] if db_entry.evidence_items else []
            roi_entry.assumptions = db_entry.assumptions_list or []
            roi_entry.confidence_level = db_entry.confidence_level or "medium"
            roi_entry.is_initiating_event = db_entry.is_initiating_event or False
            roi_entry.created_at = db_entry.created_at
            roi_entry.updated_at = db_entry.updated_at
            timeline.append(roi_entry)
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.timestamp or datetime.min)
        return timeline
    
    def _convert_evidence_items(self, db_evidence_items) -> List[Evidence]:
        """Convert database evidence items to ROI Evidence objects"""
        evidence_library = []
        
        for db_evidence in db_evidence_items:
            roi_evidence = Evidence()
            roi_evidence.id = db_evidence.id
            roi_evidence.type = db_evidence.file_type or "document"
            roi_evidence.filename = db_evidence.original_filename or db_evidence.filename
            roi_evidence.description = db_evidence.description or f"Evidence file: {roi_evidence.filename}"
            roi_evidence.source = db_evidence.source or "user_upload"
            roi_evidence.reliability = db_evidence.reliability or "medium"
            roi_evidence.timeline_refs = [entry.id for entry in db_evidence.timeline_refs] if db_evidence.timeline_refs else []
            roi_evidence.file_path = db_evidence.file_path or ""
            roi_evidence.created_at = db_evidence.created_at
            roi_evidence.updated_at = db_evidence.updated_at
            evidence_library.append(roi_evidence)
        
        return evidence_library
    
    def _convert_causal_factors(self, db_causal_factors) -> List[CausalFactor]:
        """Convert database causal factors to ROI CausalFactor objects"""
        causal_factors = []
        
        for db_factor in db_causal_factors:
            roi_factor = CausalFactor()
            roi_factor.id = db_factor.id
            roi_factor.event_id = ""  # Could be linked to timeline entries
            roi_factor.category = db_factor.category or "organizational"
            roi_factor.subcategory = ""  # Not stored in database currently
            roi_factor.title = db_factor.title
            roi_factor.description = db_factor.description
            roi_factor.evidence_support = db_factor.evidence_support_list or []
            roi_factor.analysis_text = db_factor.analysis_text or ""
            roi_factor.created_at = db_factor.created_at
            roi_factor.updated_at = db_factor.updated_at
            causal_factors.append(roi_factor)
        
        return causal_factors
    
    def _create_default_vessels(self, db_project) -> List[Vessel]:
        """Create default vessel information (can be enhanced with actual vessel data)"""
        vessels = []
        
        # For now, create a single generic vessel
        vessel = Vessel()
        vessel.official_name = "Unknown Vessel"
        vessel.identification_number = "TBD"
        vessel.flag = "United States"
        vessel.vessel_class = "Unknown"
        vessel.vessel_type = "Unknown"
        vessel.vessel_subtype = ""
        vessel.build_year = None
        vessel.gross_tonnage = None
        vessel.length = None
        vessel.beam = None
        vessel.draft = None
        vessel.propulsion = "Unknown"
        
        vessels.append(vessel)
        return vessels
    
    def _create_default_personnel(self, db_project) -> List[Personnel]:
        """Create default personnel information from timeline entries"""
        personnel = []
        personnel_names = set()
        
        # Extract unique personnel names from timeline entries
        for db_entry in db_project.timeline_entries:
            if db_entry.personnel_involved_list:
                for person_name in db_entry.personnel_involved_list:
                    if person_name and person_name.strip():
                        personnel_names.add(person_name.strip())
        
        # Create Personnel objects
        for name in personnel_names:
            person = Personnel()
            person.role = "Unknown"  # Could be enhanced with role detection
            person.vessel_assignment = "Unknown Vessel"
            person.credentials = []
            person.experience = f"Personnel: {name}"
            person.status = "uninjured"  # Default assumption
            personnel.append(person)
        
        # If no personnel found, create a placeholder
        if not personnel:
            person = Personnel()
            person.role = "Unknown"
            person.vessel_assignment = "Unknown Vessel"
            person.credentials = []
            person.experience = "Personnel information to be determined"
            person.status = "unknown"
            personnel.append(person)
        
        return personnel
    
    def _generate_roi_document(self, roi_project: InvestigationProject) -> ROIDocument:
        """Generate ROI document structure from project data"""
        roi_doc = ROIDocument()
        
        # Generate executive summary
        roi_doc.executive_summary = self._generate_executive_summary(roi_project)
        
        # Generate preliminary statement
        roi_doc.preliminary_statement = self._generate_preliminary_statement(roi_project)
        
        # Generate findings of fact from timeline
        roi_doc.findings_of_fact = self._generate_findings_from_timeline(roi_project.timeline)
        
        # Generate analysis sections from causal factors
        roi_doc.analysis_sections = self._generate_analysis_sections(roi_project.causal_factors)
        
        # Generate conclusions
        roi_doc.conclusions = self._generate_conclusions(roi_project)
        
        # Default actions and recommendations
        roi_doc.actions_taken = "Actions taken since the incident are under investigation."
        roi_doc.recommendations = "Recommendations will be provided upon completion of the investigation."
        
        return roi_doc
    
    def _generate_executive_summary(self, roi_project: InvestigationProject) -> ExecutiveSummary:
        """Generate executive summary from project data"""
        summary = ExecutiveSummary()
        
        incident_date = roi_project.incident_info.incident_date
        date_str = incident_date.strftime("%B %d, %Y") if incident_date else "an unknown date"
        
        # Scene setting paragraph
        summary.scene_setting = f"On {date_str}, {roi_project.incident_info.incident_type.lower() if roi_project.incident_info.incident_type else 'an incident'} occurred at {roi_project.incident_info.location}. This report presents the findings of the investigation conducted by {roi_project.metadata.investigating_officer}."
        
        # Outcomes paragraph
        timeline_count = len(roi_project.timeline)
        evidence_count = len(roi_project.evidence_library)
        summary.outcomes = f"The investigation analyzed {timeline_count} timeline entries and {evidence_count} pieces of evidence to determine the sequence of events and contributing factors."
        
        # Causal factors paragraph
        factor_count = len(roi_project.causal_factors)
        if factor_count > 0:
            summary.causal_factors = f"The investigation identified {factor_count} causal factors contributing to the incident. These factors have been analyzed to develop recommendations for preventing similar occurrences."
        else:
            summary.causal_factors = "Causal factor analysis is ongoing as part of this investigation."
        
        return summary
    
    def _generate_preliminary_statement(self, roi_project: InvestigationProject) -> str:
        """Generate preliminary statement"""
        return f"This report contains the preliminary findings of the investigation into the {roi_project.incident_info.incident_type.lower() if roi_project.incident_info.incident_type else 'incident'} that occurred on {roi_project.incident_info.incident_date.strftime('%B %d, %Y') if roi_project.incident_info.incident_date else 'the date in question'}. The investigation is being conducted in accordance with applicable regulations and industry standards."
    
    def _generate_findings_from_timeline(self, timeline: List[TimelineEntry]) -> List[Finding]:
        """Generate findings of fact from timeline entries"""
        findings = []
        
        for entry in timeline:
            finding = Finding()
            finding.statement = f"At {entry.timestamp.strftime('%H:%M:%S') if entry.timestamp else 'an unknown time'}, {entry.description}"
            finding.evidence_support = entry.evidence_ids
            finding.timeline_refs = [entry.id]
            finding.analysis_refs = []
            findings.append(finding)
        
        return findings
    
    def _generate_analysis_sections(self, causal_factors: List[CausalFactor]) -> List[AnalysisSection]:
        """Generate analysis sections from causal factors"""
        analysis_sections = []
        
        for factor in causal_factors:
            section = AnalysisSection()
            section.title = factor.title
            section.finding_refs = []  # Could be linked to relevant findings
            section.causal_factor_id = factor.id
            section.analysis_text = factor.analysis_text or factor.description
            section.conclusion_refs = []
            analysis_sections.append(section)
        
        return analysis_sections
    
    def _generate_conclusions(self, roi_project: InvestigationProject) -> List[Conclusion]:
        """Generate conclusions from causal factors and analysis"""
        conclusions = []
        
        # Create high-level conclusions based on causal factors
        for factor in roi_project.causal_factors:
            conclusion = Conclusion()
            conclusion.statement = f"The investigation concludes that {factor.title.lower()} was a contributing factor to the incident."
            conclusion.analysis_refs = []  # Could be linked to analysis sections
            conclusion.causal_factor_refs = [factor.id]
            conclusions.append(conclusion)
        
        # Add a general conclusion if no specific factors
        if not roi_project.causal_factors:
            conclusion = Conclusion()
            conclusion.statement = "The investigation is ongoing to determine the root causes and contributing factors of this incident."
            conclusion.analysis_refs = []
            conclusion.causal_factor_refs = []
            conclusions.append(conclusion)
        
        return conclusions
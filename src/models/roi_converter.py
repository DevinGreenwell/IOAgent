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
        """Create vessel information from project data and timeline entries"""
        vessels = []
        vessel_names = set()
        
        # Extract vessel names from timeline entries
        for db_entry in db_project.timeline_entries:
            description = db_entry.description.lower()
            # Look for common vessel name patterns
            if 'f/v ' in description:
                # Extract F/V vessel names
                import re
                matches = re.findall(r'f/v\s+([a-zA-Z0-9\s]+)', description, re.IGNORECASE)
                for match in matches:
                    clean_name = match.strip().upper()
                    if clean_name and len(clean_name) < 50:  # Reasonable name length
                        vessel_names.add(f"F/V {clean_name}")
            elif 'vessel ' in description or 'ship ' in description:
                # Look for other vessel references
                words = description.split()
                for i, word in enumerate(words):
                    if word.lower() in ['vessel', 'ship'] and i > 0:
                        potential_name = words[i-1].upper()
                        if potential_name.isalpha() and len(potential_name) > 2:
                            vessel_names.add(potential_name)
        
        # Create vessel objects from found names
        for vessel_name in vessel_names:
            vessel = Vessel()
            vessel.official_name = vessel_name
            vessel.identification_number = "O.N. [To be determined during investigation]"
            vessel.flag = "United States"
            vessel.vessel_class = "Commercial Fishing Vessel" if "F/V" in vessel_name else "Commercial Vessel"
            vessel.vessel_type = "Fishing Vessel" if "F/V" in vessel_name else "Commercial Vessel"
            vessel.vessel_subtype = "Seine Vessel" if any(word in db_project.title.lower() or any(word in entry.description.lower() for entry in db_project.timeline_entries) for word in ['seine', 'net']) else ""
            vessel.build_year = None
            vessel.gross_tonnage = None
            vessel.length = None
            vessel.beam = None
            vessel.draft = None
            vessel.propulsion = "Diesel Engine"
            vessels.append(vessel)
        
        # If no vessels found, create a generic one based on project context
        if not vessels:
            vessel = Vessel()
            vessel.official_name = f"Vessel involved in {db_project.incident_type or 'incident'}"
            vessel.identification_number = "O.N. [To be determined during investigation]"
            vessel.flag = "United States"
            vessel.vessel_class = "Commercial Vessel"
            vessel.vessel_type = "Commercial Vessel"
            vessel.vessel_subtype = ""
            vessel.build_year = None
            vessel.gross_tonnage = None
            vessel.length = None
            vessel.beam = None
            vessel.draft = None
            vessel.propulsion = "Diesel Engine"
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
        
        # Get vessel information for scene setting
        vessel_info = ""
        if roi_project.vessels and roi_project.vessels[0].official_name:
            primary_vessel = roi_project.vessels[0]
            vessel_info = f" involving the {primary_vessel.official_name}"
        
        # Scene setting paragraph - more specific
        incident_type = roi_project.incident_info.incident_type or 'marine casualty'
        location = roi_project.incident_info.location or 'under investigation'
        summary.scene_setting = f"On {date_str}, a {incident_type.lower()}{vessel_info} occurred at {location}. This report presents the findings of the investigation conducted by {roi_project.metadata.investigating_officer} in accordance with 46 CFR Part 4."
        
        # Outcomes paragraph - more descriptive based on incident type
        timeline_count = len(roi_project.timeline)
        evidence_count = len(roi_project.evidence_library)
        
        # Look for outcome indicators in timeline
        casualties_mentioned = any('deceased' in entry.description.lower() or 'injured' in entry.description.lower() or 'casualty' in entry.description.lower() for entry in roi_project.timeline)
        damage_mentioned = any('damage' in entry.description.lower() or 'collision' in entry.description.lower() or 'grounding' in entry.description.lower() for entry in roi_project.timeline)
        
        outcome_text = ""
        if casualties_mentioned and damage_mentioned:
            outcome_text = "The incident resulted in personal injury and vessel damage. "
        elif casualties_mentioned:
            outcome_text = "The incident resulted in personal injury. "
        elif damage_mentioned:
            outcome_text = "The incident resulted in vessel damage. "
        
        summary.outcomes = f"{outcome_text}The investigation examined {timeline_count} timeline entries and {evidence_count} pieces of evidence to reconstruct the sequence of events and determine the factors that contributed to this casualty."
        
        # Causal factors paragraph - more analytical
        factor_count = len(roi_project.causal_factors)
        if factor_count > 0:
            # Group factors by category for summary
            categories = set(factor.category for factor in roi_project.causal_factors if factor.category)
            if len(categories) > 1:
                summary.causal_factors = f"The causal analysis identified {factor_count} contributing factors across {len(categories)} categories of the investigation framework. These factors demonstrate the complex interactions between organizational, environmental, and operational elements that led to this incident."
            else:
                category_name = list(categories)[0] if categories else 'operational'
                summary.causal_factors = f"The investigation identified {factor_count} {category_name} factors that contributed to this incident. The analysis reveals specific areas where improvements could prevent similar casualties."
        else:
            summary.causal_factors = "Causal factor analysis is ongoing. Preliminary examination indicates multiple contributing elements that will be thoroughly analyzed to develop comprehensive recommendations."
        
        return summary
    
    def _generate_preliminary_statement(self, roi_project: InvestigationProject) -> str:
        """Generate preliminary statement"""
        incident_type = roi_project.incident_info.incident_type.lower() if roi_project.incident_info.incident_type else 'marine casualty'
        date_str = roi_project.incident_info.incident_date.strftime('%B %d, %Y') if roi_project.incident_info.incident_date else 'the date in question'
        
        statement = f"This marine casualty investigation was conducted, and this report was submitted in accordance with Title 46, Code of Federal Regulations, Subpart 4.07, and under the authority of Title 46, United States Code, Chapter 63.\n\n"
        statement += f"This report contains the preliminary findings of the investigation into the {incident_type} that occurred on {date_str}. "
        statement += f"The investigation is being conducted in accordance with 46 CFR Part 4 and follows established Coast Guard investigation procedures. "
        statement += f"The purpose of this investigation is to determine the cause of the casualty and to prevent similar incidents from occurring in the future."
        
        return statement
    
    def _generate_findings_from_timeline(self, timeline: List[TimelineEntry]) -> List[Finding]:
        """Generate findings of fact from timeline entries"""
        findings = []
        seen_descriptions = set()
        
        # Sort timeline by timestamp for logical flow
        sorted_timeline = sorted(timeline, key=lambda x: x.timestamp or datetime.min)
        
        for entry in sorted_timeline:
            # Skip duplicate descriptions
            if entry.description in seen_descriptions:
                continue
            seen_descriptions.add(entry.description)
            
            finding = Finding()
            
            # Format timestamp appropriately
            if entry.timestamp:
                time_str = entry.timestamp.strftime('%H%M on %d %B %Y')
                finding.statement = f"At {time_str}, {entry.description.rstrip('.')}"
            else:
                finding.statement = f"During the incident sequence, {entry.description.rstrip('.')}"
            
            # Add period if not present
            if not finding.statement.endswith('.'):
                finding.statement += '.'
            
            finding.evidence_support = entry.evidence_ids or []
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
        
        # Group causal factors by category for better conclusions
        factor_categories = {}
        for factor in roi_project.causal_factors:
            category = factor.category or 'other'
            if category not in factor_categories:
                factor_categories[category] = []
            factor_categories[category].append(factor)
        
        # Create category-based conclusions
        category_descriptions = {
            'organizational': 'organizational and management factors',
            'workplace': 'workplace environment and equipment factors',
            'precondition': 'precondition factors affecting crew performance',
            'production': 'unsafe acts and operational errors',
            'defense': 'failed or absent safety barriers'
        }
        
        for category, factors in factor_categories.items():
            if len(factors) == 1:
                factor = factors[0]
                conclusion = Conclusion()
                conclusion.statement = f"The investigation determined that {factor.title.lower()} contributed to this incident by {factor.description.lower() if factor.description else 'creating conditions that led to the casualty'}."
                conclusion.causal_factor_refs = [factor.id]
                conclusions.append(conclusion)
            else:
                # Multiple factors in same category
                conclusion = Conclusion()
                category_desc = category_descriptions.get(category, f'{category} factors')
                factor_titles = [f.title.lower() for f in factors]
                if len(factor_titles) == 2:
                    factors_text = f"{factor_titles[0]} and {factor_titles[1]}"
                else:
                    factors_text = f"{', '.join(factor_titles[:-1])}, and {factor_titles[-1]}"
                
                conclusion.statement = f"The investigation identified multiple {category_desc} that contributed to this incident, including {factors_text}."
                conclusion.causal_factor_refs = [f.id for f in factors]
                conclusions.append(conclusion)
        
        # Add a summary conclusion if multiple categories exist
        if len(factor_categories) > 1:
            summary_conclusion = Conclusion()
            summary_conclusion.statement = f"This incident resulted from a combination of {len(roi_project.causal_factors)} contributing factors across multiple categories of the causal analysis framework, demonstrating the complex interactions that can lead to marine casualties."
            summary_conclusion.causal_factor_refs = [f.id for f in roi_project.causal_factors]
            conclusions.append(summary_conclusion)
        
        # Add a general conclusion if no specific factors
        if not roi_project.causal_factors:
            conclusion = Conclusion()
            conclusion.statement = "The investigation is ongoing to determine the root causes and contributing factors of this incident. Additional analysis will be conducted as more information becomes available."
            conclusion.analysis_refs = []
            conclusion.causal_factor_refs = []
            conclusions.append(conclusion)
        
        return conclusions
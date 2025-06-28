# USCG-Compliant ROI Document Generator
# Follows USCG Marine Investigation Documentation and Reporting Procedures Manual standards

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from src.models.roi_models import InvestigationProject, ROIDocument, TimelineEntry, CausalFactor, Vessel, Personnel

class USCGROIGenerator:
    """USCG-compliant ROI document generator following official standards"""
    
    def __init__(self):
        self.project = None
        self.document = None
    
    def generate_roi(self, project: InvestigationProject, output_path: str) -> str:
        """Generate complete USCG-compliant ROI document"""
        self.project = project
        self.document = Document()
        
        # Set up USCG document formatting
        self._setup_uscg_formatting()
        
        # Generate USCG ROI sections in required order
        self._generate_executive_summary()
        self._generate_investigating_officers_report()
        
        # Save document
        self.document.save(output_path)
        return output_path
    
    def _setup_uscg_formatting(self):
        """Set up USCG-required document formatting"""
        # Set default font to Times New Roman 12-pitch as required
        style = self.document.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        
        # Set paragraph spacing
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.line_spacing = 1.0
        
        # Set margins to 1 inch
        sections = self.document.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
    
    def _format_date(self, date: datetime) -> str:
        """Format date according to USCG standard: Month DD, YYYY"""
        if date:
            return date.strftime("%B %d, %Y")
        return "[Date to be determined]"
    
    def _format_time(self, time: datetime) -> str:
        """Format time according to USCG standard: HHMM in 24-hour format"""
        if time:
            return time.strftime("%H%M")
        return "[Time unknown]"
    
    def _italicize_vessel_names(self, text: str) -> str:
        """Helper to mark vessel names for italicization"""
        # This is a placeholder - actual italicization happens when adding to document
        return text
    
    def _generate_executive_summary(self):
        """Generate Executive Summary section per USCG standards"""
        # Generate title in USCG format
        title = self._generate_uscg_title()
        
        # Title paragraph
        title_para = self.document.add_paragraph()
        title_para.add_run(title).bold = True
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add spacing
        self.document.add_paragraph()
        
        # Executive Summary heading
        summary_heading = self.document.add_paragraph()
        summary_heading.add_run("EXECUTIVE SUMMARY").bold = True
        summary_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        self.document.add_paragraph()
        
        # Paragraph 1: Scene Setting
        scene_para = self._generate_scene_setting_paragraph()
        self.document.add_paragraph(scene_para)
        
        self.document.add_paragraph()  # Space between paragraphs
        
        # Paragraph 2: Outcomes
        outcomes_para = self._generate_outcomes_paragraph()
        self.document.add_paragraph(outcomes_para)
        
        self.document.add_paragraph()  # Space between paragraphs
        
        # Paragraph 3: Causal Factors
        causal_para = self._generate_causal_factors_paragraph()
        self.document.add_paragraph(causal_para)
        
        self.document.add_page_break()
    
    def _generate_uscg_title(self) -> str:
        """Generate title in USCG format using Investigation Title and Official Number"""
        # Use Investigation Title and Official Number from project info
        investigation_title = self.project.metadata.title or "VESSEL INCIDENT"
        official_number = getattr(self.project, 'official_number', None)
        
        # Format official number
        if official_number and official_number != 'N/A':
            on_text = f"(O.N. {official_number})"
        else:
            on_text = ""
        
        # Build title in USCG format
        vessel_text = f"{investigation_title.upper()} {on_text}".strip()
        
        # Determine casualty type with injuries/fatalities
        casualty_type = self.project.incident_info.incident_type or "MARINE CASUALTY"
        
        # Check for personnel casualties
        has_injuries = False
        has_fatalities = False
        
        for entry in self.project.timeline:
            desc_lower = entry.description.lower()
            if any(word in desc_lower for word in ['injured', 'injury', 'injuries']):
                has_injuries = True
            if any(word in desc_lower for word in ['deceased', 'death', 'fatality', 'died']):
                has_fatalities = True
        
        if has_fatalities:
            casualty_desc = f"{casualty_type.upper()} WITH LOSS OF LIFE"
        elif has_injuries:
            casualty_desc = f"{casualty_type.upper()} WITH INJURIES"
        else:
            casualty_desc = casualty_type.upper()
        
        # Location
        location = self.project.incident_info.location or "LOCATION"
        if "near" not in location.lower() and "on" not in location.lower():
            location = f"ON {location.upper()}"
        else:
            location = location.upper()
        
        # Date
        date_str = self._format_date(self.project.incident_info.incident_date).upper()
        
        return f"{vessel_text}, {casualty_desc} {location} ON {date_str}"
    
    def _generate_scene_setting_paragraph(self) -> str:
        """Generate paragraph 1 of Executive Summary - Scene Setting"""
        # Get incident date and time
        incident_date = self._format_date(self.project.incident_info.incident_date)
        
        # Find the earliest timeline entry for departure/start
        earliest_entry = None
        if self.project.timeline:
            sorted_timeline = sorted(self.project.timeline, key=lambda x: x.timestamp or datetime.max)
            earliest_entry = sorted_timeline[0] if sorted_timeline else None
        
        # Build scene setting
        if earliest_entry and earliest_entry.timestamp:
            time_str = self._format_time(earliest_entry.timestamp)
            opening = f"On {incident_date}, at {time_str}, "
        else:
            opening = f"On {incident_date}, "
        
        # Get vessel name
        vessel_name = ""
        if self.project.vessels and self.project.vessels[0].official_name:
            vessel_name = f"the {self.project.vessels[0].official_name} "
        
        # Extract key scene-setting details from timeline
        scene_details = []
        for entry in self.project.timeline[:5]:  # Look at first few entries
            if any(word in entry.description.lower() for word in ['departed', 'began', 'started', 'commenced']):
                scene_details.append(entry.description)
                break
        
        if scene_details:
            scene = opening + vessel_name + scene_details[0].lower()
        else:
            scene = opening + vessel_name + f"was operating in {self.project.incident_info.location}"
        
        # Add what happened
        incident_type = self.project.incident_info.incident_type or "an incident"
        scene += f". {self._describe_incident_from_timeline()}"
        
        return scene
    
    def _generate_outcomes_paragraph(self) -> str:
        """Generate paragraph 2 of Executive Summary - Outcomes"""
        outcomes = []
        
        # Scan timeline for outcomes
        for entry in self.project.timeline:
            desc_lower = entry.description.lower()
            
            # Personnel casualties
            if 'deceased' in desc_lower or 'died' in desc_lower or 'death' in desc_lower:
                if 'pronounced' in desc_lower:
                    outcomes.append(entry.description)
                else:
                    outcomes.append("resulted in loss of life")
            elif 'injured' in desc_lower or 'injury' in desc_lower:
                outcomes.append("resulted in personnel injuries")
            
            # Vessel damage
            elif any(word in desc_lower for word in ['damage', 'holed', 'flooded', 'fire', 'explosion']):
                outcomes.append("resulted in vessel damage")
            
            # Environmental
            elif any(word in desc_lower for word in ['spill', 'discharge', 'pollution']):
                outcomes.append("resulted in environmental impact")
        
        # Build outcomes paragraph
        if outcomes:
            # Use the most specific outcome found
            outcome_text = outcomes[0] if outcomes[0].startswith("resulted") else outcomes[0]
            para = f"The {outcome_text}."
        else:
            para = f"The incident resulted in a marine casualty requiring investigation under 46 CFR Part 4."
        
        # Add response/rescue information if available
        response_entries = [e for e in self.project.timeline if any(word in e.description.lower() 
                           for word in ['coast guard', 'rescue', 'evacuated', 'transported', 'ems', 'medical'])]
        
        if response_entries:
            para += f" {response_entries[0].description}"
        
        return para
    
    def _generate_causal_factors_paragraph(self) -> str:
        """Generate paragraph 3 of Executive Summary - Causal Factors"""
        # Identify initiating event
        initiating_event = None
        for entry in self.project.timeline:
            if entry.is_initiating_event or entry.type == 'event':
                initiating_event = entry
                break
        
        para = "Through its investigation, the Coast Guard determined "
        
        if initiating_event:
            para += f"the initiating event for this casualty was {initiating_event.description.lower()}. "
        else:
            para += f"the cause of this casualty. "
        
        # List causal factors
        if self.project.causal_factors:
            factor_titles = []
            for i, factor in enumerate(self.project.causal_factors):
                factor_titles.append(f"({i+1}) {factor.title}")
            
            para += f"Causal factors contributing to this casualty include: {', '.join(factor_titles)}."
        else:
            para += "Contributing factors are under investigation."
        
        return para
    
    def _describe_incident_from_timeline(self) -> str:
        """Extract incident description from timeline"""
        # Look for event type entries that describe what happened
        for entry in self.project.timeline:
            if entry.type == 'event' or entry.is_initiating_event:
                # Clean up the description
                desc = entry.description
                if desc[0].isupper():
                    desc = desc[0].lower() + desc[1:]
                return f"At {self._format_time(entry.timestamp)}, {desc}"
        
        # Fallback
        incident_type = self.project.incident_info.incident_type or "a marine casualty"
        return f"A {incident_type.lower()} occurred"
    
    def _generate_investigating_officers_report(self):
        """Generate the main Investigating Officer's Report"""
        # Header for IO Report
        p = self.document.add_paragraph()
        p.add_run("Commandant\n")
        p.add_run("United States Coast Guard\n")
        p.add_run(f"Sector {self.project.incident_info.location or 'Investigation'}\n")
        p.add_run("Unit Address\n")
        p.add_run("Unit Address\n")
        p.add_run("Staff Symbol: \n")
        p.add_run("Phone: \n")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # Add spacing
        self.document.add_paragraph()
        self.document.add_paragraph()
        
        # Add date and control number
        p = self.document.add_paragraph()
        p.add_run("16732\n")
        p.add_run(self._format_date(datetime.now()))
        
        # Add spacing
        self.document.add_paragraph()
        self.document.add_paragraph()
        
        # Title
        title = self._generate_uscg_title()
        title_para = self.document.add_paragraph()
        title_para.add_run(title).bold = True
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        self.document.add_paragraph()
        
        # INVESTIGATING OFFICER'S REPORT heading
        report_heading = self.document.add_paragraph()
        report_heading.add_run("INVESTIGATING OFFICER'S REPORT").bold = True
        report_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        self.document.add_paragraph()
        
        # Generate all required sections
        self._generate_section_1_preliminary_statement()
        self._generate_section_2_vessels_involved()
        self._generate_section_3_personnel_casualties()
        self._generate_section_4_findings_of_fact()
        self._generate_section_5_analysis()
        self._generate_section_6_conclusions()
        self._generate_section_7_actions_taken()
        self._generate_section_8_recommendations()
        
        # Add signature block
        self._generate_signature_block()
    
    def _generate_section_1_preliminary_statement(self):
        """Section 1: Preliminary Statement"""
        # Section heading
        heading = self.document.add_paragraph()
        heading.add_run("1. Preliminary Statement").bold = True
        
        # 1.1 - Authority statement
        self.document.add_paragraph(
            "1.1. This marine casualty investigation was conducted and this report was submitted in "
            "accordance with Title 46, Code of Federal Regulations (CFR), Subpart 4.07, and under the "
            "authority of Title 46, United States Code (USC) Chapter 63."
        )
        
        # 1.2 - Parties in interest (if any)
        parties = []
        if self.project.vessels:
            for vessel in self.project.vessels:
                if vessel.official_name:
                    parties.append(f"the owner of the {vessel.official_name}")
        
        # Add personnel as parties if involved
        for person in self.project.personnel:
            if person.role.lower() in ['master', 'captain', 'operator']:
                parties.append(f"the {person.role.lower()}")
        
        if parties:
            parties_text = ", ".join(parties)
            self.document.add_paragraph(
                f"1.2. The Investigating Officer designated {parties_text}, as parties-in-interest in this "
                f"investigation. No other individuals, organizations, or parties were designated a party-in-"
                f"interest in accordance with 46 CFR Subsection 4.03-10."
            )
        
        # 1.3 - Lead agency statement
        self.document.add_paragraph(
            "1.3. The Coast Guard was lead agency for all evidence collection activities involving this "
            "investigation."
        )
        
        # Check for loss of life
        has_fatality = any('deceased' in e.description.lower() or 'death' in e.description.lower() 
                          for e in self.project.timeline)
        
        if has_fatality:
            self.document.add_paragraph(
                "Due to this investigation involving a loss of life, the Coast Guard Investigative "
                "Service (CGIS) was notified and agreed to provide technical assistance as required."
            )
        
        self.document.add_paragraph(
            "No other persons or organizations assisted in this investigation."
        )
        
        # 1.4 - Time format statement
        self.document.add_paragraph(
            "1.4. All times listed in this report are approximate, and in Eastern Standard Time using a 24-"
            "hour format."
        )
        
        self.document.add_paragraph()  # Add spacing
    
    def _generate_section_2_vessels_involved(self):
        """Section 2: Vessels Involved in the Incident"""
        heading = self.document.add_paragraph()
        heading.add_run("2. Vessels Involved in the Incident").bold = True
        
        for vessel in self.project.vessels:
            # Add photo placeholder
            self.document.add_paragraph()
            photo_para = self.document.add_paragraph()
            photo_para.add_run("Figure 1. Undated Photograph of Vessel").italic = True
            self.document.add_paragraph()
            
            # Create vessel information table
            table = self.document.add_table(rows=13, cols=2)
            table.style = 'Table Grid'
            
            # Populate vessel information in table format
            vessel_info = [
                ("Official Name:", vessel.official_name or 'Unknown'),
                ("", f"({vessel.official_name.upper() if vessel.official_name else 'VESSEL NAME'})"),
                ("Identification Number:", f"{vessel.identification_number or '0000000'} - Official Number (US)"),
                ("Flag:", vessel.flag or 'United States'),
                ("Vessel Class/Type/Sub-Type", f"{vessel.vessel_class or 'Unknown'}/{vessel.vessel_type or 'Unknown'}/{vessel.vessel_subtype or 'N/A'}"),
                ("Build Year:", vessel.build_year or 'YYYY'),
                ("Gross Tonnage:", f"{vessel.gross_tonnage or '##'} GT"),
                ("Length:", f"{vessel.length or '##'} feet"),
                ("Beam/Width:", f"{vessel.beam or '##'} feet"),
                ("Draft/Depth:", f"{vessel.draft or '##'} feet"),
                ("Main/Primary Propulsion:", vessel.propulsion or 'Configuration/System Type, Ahead Horse Power'),
                ("Owner:", f"{vessel.owner or 'Line 1 = Official Name'}\n{vessel.owner_location or 'Line 2 = City, State/Country'}"),
                ("Operator:", f"{vessel.operator or 'Line 1 = Official Name'}\n{vessel.operator_location or 'Line 2 = City, State/Country'}")
            ]
            
            # Fill table with vessel information
            for i, (label, value) in enumerate(vessel_info):
                row = table.rows[i]
                row.cells[0].text = label
                row.cells[1].text = value
                # Make vessel name italic in second row
                if i == 1:
                    for run in row.cells[1].paragraphs[0].runs:
                        run.italic = True
            
            self.document.add_paragraph()  # Spacing between vessels
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_section_3_personnel_casualties(self):
        """Section 3: Deceased, Missing, and/or Injured Persons"""
        heading = self.document.add_paragraph()
        heading.add_run("3. Deceased, Missing, and/or Injured Persons").bold = True
        
        # Create table for personnel casualties
        if any(p.status.lower() in ['deceased', 'missing', 'injured'] for p in self.project.personnel):
            table = self.document.add_table(rows=1, cols=4)
            table.style = 'Light Grid'
            
            # Header row
            header_cells = table.rows[0].cells
            header_cells[0].text = "Relationship to Vessel"
            header_cells[1].text = "Sex"
            header_cells[2].text = "Age"
            header_cells[3].text = "Status"
            
            # Add personnel entries
            for person in self.project.personnel:
                if person.status.lower() in ['deceased', 'missing', 'injured']:
                    row_cells = table.add_row().cells
                    row_cells[0].text = person.role or "Unknown"
                    row_cells[1].text = "Unknown"  # Sex not tracked in our model
                    row_cells[2].text = "Unknown"  # Age not tracked in our model
                    row_cells[3].text = person.status.title()
        else:
            self.document.add_paragraph("No personnel casualties resulted from this incident.")
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_section_4_findings_of_fact(self):
        """Section 4: Findings of Fact"""
        heading = self.document.add_paragraph()
        heading.add_run("4. Findings of Fact").bold = True
        
        # 4.1 The Incident
        subheading = self.document.add_paragraph()
        subheading.add_run("4.1. The Incident:").bold = True
        
        # Generate professional findings from timeline using AI - ENHANCED VERSION
        if self.project.roi_document.findings_of_fact:
            # Use existing findings if available
            finding_number = 1
            for finding in self.project.roi_document.findings_of_fact:
                para = self.document.add_paragraph(f"4.1.{finding_number}. {finding.statement}")
                finding_number += 1
        else:
            # Generate comprehensive findings from timeline using AI
            from src.models.ai_assistant import AIAssistant
            ai_assistant = AIAssistant()
            
            if ai_assistant.client and self.project.timeline:
                # Convert timeline entries to appropriate format
                timeline_objects = []
                for entry in self.project.timeline:
                    timeline_objects.append(entry)
                
                evidence_objects = []
                for evidence in self.project.evidence_library:
                    evidence_objects.append(evidence)
                
                # Generate professional findings using AI
                findings_statements = ai_assistant.generate_findings_of_fact_from_timeline(timeline_objects, evidence_objects)
                
                # Add AI-generated findings with proper numbering
                finding_number = 1
                for finding_statement in findings_statements:
                    # Ensure proper numbering format
                    if not finding_statement.strip().startswith('4.1.'):
                        finding_text = f"4.1.{finding_number}. {finding_statement.strip()}"
                        finding_number += 1
                    else:
                        finding_text = finding_statement.strip()
                    
                    para = self.document.add_paragraph(finding_text)
                
                # If no AI findings generated, use enhanced fallback
                if not findings_statements:
                    self._generate_enhanced_findings_from_timeline()
            else:
                # Enhanced fallback method
                self._generate_enhanced_findings_from_timeline()
        
        # 4.2 Additional/Supporting Information (if needed)
        if self.project.evidence_library:
            self.document.add_paragraph()
            subheading = self.document.add_paragraph()
            subheading.add_run("4.2. Additional/Supporting Information:").bold = True
            
            # Add evidence summary
            for i, evidence in enumerate(self.project.evidence_library, 1):
                self.document.add_paragraph(
                    f"4.2.{i}. Evidence item: {evidence.filename} - {evidence.description}"
                )
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_enhanced_findings_from_timeline(self):
        """Enhanced method for professional timeline to findings conversion"""
        if not self.project.timeline:
            self.document.add_paragraph("4.1.1. No timeline entries have been documented for this incident.")
            return
        
        # Sort timeline by timestamp
        sorted_timeline = sorted(
            [entry for entry in self.project.timeline if entry.timestamp],
            key=lambda x: x.timestamp
        )
        
        finding_number = 1
        for entry in sorted_timeline:
            # Format timestamp in USCG style
            time_str = self._format_date(entry.timestamp) + f", at {self._format_time(entry.timestamp)}"
            
            # Create professional finding statement with enhanced formatting
            description = entry.description
            if not description.endswith('.'):
                description += '.'
            
            # Capitalize first letter for professional presentation
            if description and description[0].islower():
                description = description[0].upper() + description[1:]
            
            finding_text = f"4.1.{finding_number}. On {time_str}, {description}"
            self.document.add_paragraph(finding_text)
            finding_number += 1
    
    def _generate_section_5_analysis(self):
        """Section 5: Analysis - THE MOST CRITICAL SECTION OF THE ROI"""
        # Add emphasis that this is the most important section
        heading = self.document.add_paragraph()
        heading.add_run("5. Analysis").bold = True
        
        # Add introductory note about the analysis section
        intro_para = self.document.add_paragraph()
        intro_para.add_run("The following analysis examines the causal factors that contributed to this marine casualty. Each factor is supported by findings of fact documented in Section 4 above.")
        self.document.add_paragraph()  # Extra spacing
        
        # Check if we have causal factors to analyze
        if not self.project.causal_factors:
            # Generate a placeholder analysis section if no factors exist
            self.document.add_paragraph("No causal factors have been identified for analysis at this time. Further investigation may be required to determine contributing factors.")
            self.document.add_paragraph()
            return
        
        # Generate analysis for each causal factor with enhanced formatting
        analysis_number = 1
        for factor in self.project.causal_factors:
            # Analysis heading with negative phrasing emphasis
            subheading = self.document.add_paragraph()
            
            # Ensure negative phrasing in title
            title = factor.title
            if not any(title.lower().startswith(phrase) for phrase in ['failure', 'lack', 'inadequate', 'absence', 'deficiency']):
                if 'failure' not in title.lower() and 'lack' not in title.lower():
                    title = f"Failure to properly address: {title}"
            
            subheading_run = subheading.add_run(f"5.{analysis_number}. {title}")
            subheading_run.bold = True
            subheading_run.font.size = Pt(12)
            
            # Enhanced analysis text with findings references
            analysis_para = self.document.add_paragraph()
            analysis_text = factor.analysis_text or factor.description
            
            # Ensure comprehensive analysis explaining HOW and WHY
            if "contributed to" not in analysis_text.lower() and "led to" not in analysis_text.lower():
                analysis_text += f" This {factor.category} factor directly contributed to the marine casualty by creating conditions that allowed the incident sequence to proceed and prevented effective mitigation of the hazard."
            
            # Add evidence references if available
            if hasattr(factor, 'evidence_support_list') and factor.evidence_support_list:
                analysis_text += f" This conclusion is supported by evidence from the investigation files."
            
            analysis_para.add_run(analysis_text)
            
            # Add factor category information
            category_para = self.document.add_paragraph()
            category_para.add_run(f"Category: {factor.category.title()} Factor").italic = True
            
            # Add spacing between analyses for clarity
            self.document.add_paragraph()
            analysis_number += 1
    
        self.document.add_paragraph()  # Section spacing
    
    def _generate_section_6_conclusions(self):
        """Section 6: Conclusions"""
        heading = self.document.add_paragraph()
        heading.add_run("6. Conclusions").bold = True
        
        # 6.1 Determination of Cause
        subheading = self.document.add_paragraph()
        subheading.add_run("6.1. Determination of Cause:").bold = True
        
        # Generate comprehensive conclusions based on analysis
        if hasattr(self.project, 'roi_document') and self.project.roi_document.conclusions:
            # Use existing conclusions if available
            for i, conclusion in enumerate(self.project.roi_document.conclusions, 1):
                self.document.add_paragraph(f"6.1.{i}. {conclusion.statement}")
        else:
            # Generate conclusions from causal factors and timeline
            conclusion_number = 1
            
            # Find initiating event
            initiating_event = None
            for entry in self.project.timeline:
                if hasattr(entry, 'is_initiating_event') and entry.is_initiating_event:
                    initiating_event = entry
                    break
            
            if initiating_event:
                self.document.add_paragraph(f"6.1.{conclusion_number}. The Coast Guard determines that the initiating event for this marine casualty was {initiating_event.description.lower()}.")
                conclusion_number += 1
            
            # Add causal factor conclusions
            if self.project.causal_factors:
                causal_factors_text = ", ".join([f.title.lower() for f in self.project.causal_factors[:3]])  # Limit to top 3
                self.document.add_paragraph(f"6.1.{conclusion_number}. Contributing causal factors included: {causal_factors_text}.")
                conclusion_number += 1
                
                # Add prevention conclusion
                self.document.add_paragraph(f"6.1.{conclusion_number}. This casualty could have been prevented through proper implementation of established safety procedures and adherence to regulatory requirements.")
            else:
                self.document.add_paragraph(f"6.1.{conclusion_number}. The exact cause of this marine casualty requires further investigation to determine contributing factors.")
        
        # 6.2-6.6 Standard enforcement sections (required by USCG format)
        self.document.add_paragraph()
        self.document.add_paragraph("6.2. Evidence of Act(s) or Violation(s) of Law by Any Coast Guard "
                                  "Credentialed Mariner Subject to Action Under 46 USC Chapter 77: None identified.")
        
        self.document.add_paragraph("6.3. Evidence of Act(s) or Violation(s) of Law by U.S. Coast Guard "
                                  "Personnel, or any other person: None identified.")
        
        self.document.add_paragraph("6.4. Evidence of Act(s) Subject to Civil Penalty: None identified.")
        
        self.document.add_paragraph("6.5. Evidence of Criminal Act(s): None identified.")
        
        self.document.add_paragraph("6.6. Need for New or Amended U.S. Law or Regulation: None identified.")
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_section_7_actions_taken(self):
        """Section 7: Actions Taken Since the Incident"""
        heading = self.document.add_paragraph()
        heading.add_run("7. Actions Taken Since the Incident").bold = True
        
        if self.project.roi_document.actions_taken:
            self.document.add_paragraph(self.project.roi_document.actions_taken)
        else:
            self.document.add_paragraph(
                "7.1. The Coast Guard has initiated safety awareness campaigns to prevent similar incidents."
            )
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_section_8_recommendations(self):
        """Section 8: Recommendations"""
        heading = self.document.add_paragraph()
        heading.add_run("8. Recommendations").bold = True
        
        # 8.1 Safety Recommendations
        subheading = self.document.add_paragraph()
        subheading.add_run("8.1. Safety Recommendations:").bold = True
        
        if hasattr(self.project, 'roi_document') and self.project.roi_document.recommendations:
            self.document.add_paragraph(self.project.roi_document.recommendations)
        else:
            # Generate comprehensive recommendations based on causal factors
            if self.project.causal_factors:
                rec_number = 1
                for factor in self.project.causal_factors:
                    if factor.category == 'organization':
                        self.document.add_paragraph(
                            f"8.1.{rec_number}. The Coast Guard recommends that vessel owners and operators review and strengthen organizational safety management systems to prevent {factor.title.lower()}. This should include enhanced safety policies, procedures, and training programs."
                        )
                    elif factor.category == 'workplace':
                        self.document.add_paragraph(
                            f"8.1.{rec_number}. The Coast Guard recommends implementing workplace safety improvements including equipment upgrades, environmental controls, and procedural modifications to mitigate {factor.title.lower()}."
                        )
                    elif factor.category == 'precondition':
                        self.document.add_paragraph(
                            f"8.1.{rec_number}. The Coast Guard recommends enhanced crew training, fatigue management, and operational planning to address preconditions that led to {factor.title.lower()}."
                        )
                    elif factor.category == 'production':
                        self.document.add_paragraph(
                            f"8.1.{rec_number}. The Coast Guard recommends improved operational procedures and enhanced crew competency training to prevent {factor.title.lower()}."
                        )
                    elif factor.category == 'defense':
                        self.document.add_paragraph(
                            f"8.1.{rec_number}. The Coast Guard recommends strengthening safety barriers and defense mechanisms to prevent {factor.title.lower()}. This includes backup systems, emergency procedures, and fail-safe devices."
                        )
                    rec_number += 1
            else:
                # Default recommendation when no specific factors identified
                self.document.add_paragraph(
                    "8.1.1. The Coast Guard recommends that vessel owners and operators review their safety management systems and ensure compliance with all applicable regulations to prevent similar marine casualties."
                )
        
        # 8.2 Administrative Recommendations
        self.document.add_paragraph()
        subheading = self.document.add_paragraph()
        subheading.add_run("8.2. Administrative Recommendations:").bold = True
        self.document.add_paragraph("None at this time.")
        
        self.document.add_paragraph()  # Section spacing
    
    def _generate_signature_block(self):
        """Generate signature block"""
        # Add spacing
        for _ in range(3):
            self.document.add_paragraph()
        
        # Signature line
        self.document.add_paragraph("_" * 50)
        
        # Name and title
        officer_name = self.project.metadata.investigating_officer or "[Investigating Officer Name]"
        self.document.add_paragraph(officer_name.upper())
        self.document.add_paragraph("Lieutenant, U.S. Coast Guard")
        self.document.add_paragraph("Investigating Officer")
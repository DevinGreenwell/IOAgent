"""AI prompt building utilities for IOAgent."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models.roi_models import InvestigationProject, CausalFactor, TimelineEntry

# Style snippet for USCG reports
STYLE_SNIPPET = """
Marine Casualty: F/V EXAMPLE FISHER, O.N. 123456; Injury in Gulf of Alaska on September 15, 2024

1. EXECUTIVE SUMMARY

On September 15, 2024, at approximately 1430 hours Alaska Daylight Time, a commercial fisherman was struck by a hook onboard the fishing vessel EXAMPLE FISHER while conducting fishing operations in the Gulf of Alaska...

CAUSAL FACTORS THAT CONTRIBUTED TO THE CASUALTY:
• ORGANIZATION. The vessel owner did not ensure adequate safety management systems...
• WORKPLACE. The working deck configuration created line-of-fire hazards...
• PRODUCTION. Time pressure to deploy gear before weather deteriorated led to rushed operations...

2. INVESTIGATING OFFICER'S REPORT

On September 15, 2024, at approximately 1430 hours...
"""

class AIPromptBuilder:
    """Builds structured prompts for AI analysis."""
    
    @staticmethod
    def build_vessel_info(project: InvestigationProject) -> List[str]:
        """Extract vessel information from project."""
        vessel_info = []
        if hasattr(project, 'vessels'):
            for vessel in project.vessels:
                vessel_info.append(f"- {vessel.official_name} (O.N. {vessel.identification_number})")
        return vessel_info
    
    @staticmethod
    def build_timeline_text(project: InvestigationProject, limit: int = 20) -> List[str]:
        """Build timeline text from project timeline entries."""
        timeline_text = []
        if hasattr(project, 'timeline'):
            sorted_timeline = sorted(project.timeline, key=lambda x: x.timestamp or datetime.min)[:limit]
            for entry in sorted_timeline:
                if entry.timestamp:
                    timeline_text.append(
                        f"- {entry.timestamp.strftime('%B %d, %Y at %H%M')}: {entry.description}"
                    )
        return timeline_text
    
    @staticmethod
    def build_causal_factors_text(project: InvestigationProject) -> List[str]:
        """Build causal factors text from project."""
        causal_factors_text = []
        if hasattr(project, 'causal_factors'):
            for factor in project.causal_factors:
                causal_factors_text.append(f"- {factor.category.upper()}: {factor.title}")
        return causal_factors_text
    
    @staticmethod
    def build_incident_info(project: InvestigationProject) -> Dict[str, str]:
        """Extract incident information from project."""
        info = {
            'type': 'Unknown',
            'location': 'Unknown',
            'date': 'Unknown'
        }
        
        if hasattr(project, 'incident_info') and project.incident_info:
            info['type'] = project.incident_info.incident_type or 'Unknown'
            info['location'] = project.incident_info.location or 'Unknown'
            if project.incident_info.incident_date:
                info['date'] = project.incident_info.incident_date.strftime('%B %d, %Y')
        
        return info
    
    @staticmethod
    def build_complete_roi_prompt(project: InvestigationProject) -> str:
        """Build complete ROI generation prompt."""
        vessel_info = AIPromptBuilder.build_vessel_info(project)
        timeline_text = AIPromptBuilder.build_timeline_text(project)
        causal_factors_text = AIPromptBuilder.build_causal_factors_text(project)
        incident_info = AIPromptBuilder.build_incident_info(project)
        
        return f"""
EXEMPLAR (mirror headings, tone, and numbering):
{STYLE_SNIPPET}

---
Generate professional USCG Report of Investigation sections based on this incident data. Match the professional style of actual USCG reports.

INCIDENT INFORMATION:
Type: {incident_info['type']}
Location: {incident_info['location']}
Date: {incident_info['date']}
Vessels: {', '.join(vessel_info) if vessel_info else 'Unknown'}

KEY TIMELINE EVENTS:
{chr(10).join(timeline_text) if timeline_text else 'No timeline available'}

IDENTIFIED CAUSAL FACTORS:
{chr(10).join(causal_factors_text) if causal_factors_text else 'No causal factors identified'}

Generate the following ROI sections in JSON format:

1. EXECUTIVE SUMMARY (3 comprehensive paragraphs):
   
   PARAGRAPH 1 - SCENE SETTING AND INCIDENT NARRATIVE (4-6 sentences):
   Create a compelling narrative that tells the complete story. Include:
   - Date, time, and location with specific details
   - Who was involved (vessel name, crew details, operational context)
   - What maritime activity was taking place (fishing operations, transit, etc.)
   - The operational environment and conditions
   - Build up to and describe the main incident/casualty
   
   PARAGRAPH 2 - IMMEDIATE CONSEQUENCES AND RESPONSE (3-5 sentences):
   Detail what happened immediately after:
   - Injuries sustained and their severity
   - Damage to vessel or equipment
   - Emergency response actions taken
   - Initial outcomes and immediate impacts
   
   PARAGRAPH 3 - INVESTIGATION FINDINGS AND PREVENTION (4-6 sentences):
   Summarize the investigation's conclusions:
   - Start with "The investigation revealed..."
   - Present causal factors in flowing narrative (not bullets)
   - Explain HOW these factors led to the casualty
   - Connect the causes to the outcome
   - End with forward-looking prevention focus

2. CAUSAL FACTORS THAT CONTRIBUTED TO THE CASUALTY (subsection of Executive Summary):
   List in this specific order:
   • ORGANIZATION. [How organizational failures contributed]
   • WORKPLACE. [Environmental/physical factors]
   • PRODUCTION. [Operational pressures or procedures]
   • PRECONDITION. [Individual state/condition factors if applicable]
   • DEFENSE. [Failed barriers or safeguards if applicable]

3. INVESTIGATING OFFICER'S REPORT:
   Professional narrative (2-3 paragraphs) that:
   - Opens with date/time/location
   - Describes the vessel and operation
   - Details the sequence of events
   - Includes specific facts and observations
   - Maintains objective, factual tone

4. FINDINGS OF FACT:
   Numbered list (at least 10 items) of specific, verifiable facts:
   - Vessel particulars and documentation
   - Personnel qualifications and experience
   - Equipment condition and maintenance
   - Environmental conditions
   - Specific timeline of events
   - Regulatory compliance status

5. ACTIONS TAKEN:
   List of concrete actions taken by:
   - The Investigating Officer
   - The vessel owner/operator
   - Other involved parties

6. RECOMMENDATIONS:
   Specific, actionable recommendations for:
   - The vessel owner/operator
   - Industry best practices
   - Regulatory considerations

Return as properly formatted JSON with keys: executive_summary, causal_factors, investigating_officers_report, findings_of_fact, actions_taken, recommendations
"""
    
    @staticmethod
    def build_timeline_suggestion_prompt(evidence_text: str, filename: str, existing_timeline: Optional[List[Any]] = None) -> str:
        """Build prompt for timeline suggestion from evidence."""
        # Build existing timeline text if provided
        existing_entries = ""
        if existing_timeline:
            entries = []
            for entry in existing_timeline:
                if hasattr(entry, 'timestamp') and entry.timestamp:
                    entries.append(
                        f"- {entry.timestamp}: {entry.type.title() if hasattr(entry, 'type') else ''} - "
                        f"{entry.description if hasattr(entry, 'description') else ''}"
                    )
                elif isinstance(entry, dict) and entry.get('timestamp'):
                    entries.append(
                        f"- {entry.get('timestamp')}: {entry.get('type', '').title()} - "
                        f"{entry.get('description', '')}"
                    )
            if entries:
                existing_entries = "\n".join(entries)
        
        # Limit evidence text to prevent token overflow
        evidence_excerpt = evidence_text[:15000] if len(evidence_text) > 15000 else evidence_text
        
        return f"""Extract timeline entries from this marine casualty investigation document. This document may contain structured timeline data with precise timestamps, types, and detailed descriptions.

PRIORITY EXTRACTION PATTERNS:
1. **Structured Timeline Entries**: Look for explicit timeline blocks with:
   - Precise timestamps (e.g., "01Aug2023 14:15:40 Z", "08:00:00 Z") 
   - Timeline Type/Subtype classifications (Action, Condition, Event)
   - Detailed subject and description information
   - Location coordinates and details

2. **Narrative Timeline Elements**: Extract from prose descriptions:
   - Time references ("at approximately 0630", "during the third set")
   - Sequence indicators ("soon thereafter", "when", "after")
   - Action descriptions with temporal context

3. **Event Classifications**: Identify and properly categorize:
   - ACTIONS: Crew decisions, equipment operations, communications, navigation
   - CONDITIONS: Weather, vessel status, personnel factors, environmental state  
   - EVENTS: Casualties, groundings, equipment failures, incidents

DOCUMENT: {filename}
CONTENT:
{evidence_excerpt}

{f"EXISTING TIMELINE (avoid duplicates):{chr(10)}{existing_entries}" if existing_entries else ""}

EXTRACTION REQUIREMENTS:
- Preserve precise timestamps when available (convert formats like "01Aug2023 14:15:40 Z" to "2023-08-01 14:15:40")
- Use exact descriptions from source document when possible
- Extract ALL timeline-relevant information, not just major events
- Include personnel involved, locations, and technical details
- Capture both pre-incident conditions and post-incident actions

Return a JSON array of timeline entries with enhanced detail:
[
  {{
    "timestamp": "2023-08-01 14:15:40",
    "type": "event|action|condition",
    "description": "Detailed description from source document", 
    "confidence": "high|medium|low",
    "personnel_involved": ["Names or roles of people involved"],
    "location": "Specific location if mentioned",
    "source_reference": "Page or section reference if available",
    "assumptions": ["Any logical assumptions made about timing or details"],
    "is_initiating_event": false
  }}
]

CRITICAL: If the document contains structured timeline sections with explicit timestamps and classifications, extract ALL entries from those sections. These are high-quality, verified timeline data points that should be prioritized over narrative extraction.

Return ONLY the JSON array, no other text."""
    
    @staticmethod
    def build_causal_analysis_prompt(timeline: List[Any], evidence: List[Any]) -> str:
        """Build prompt for causal analysis using USCG methodology."""
        # Separate initiating event from subsequent events
        initiating_events = []
        subsequent_events = []
        for entry in timeline:
            if hasattr(entry, 'is_initiating_event') and entry.is_initiating_event:
                initiating_events.append(entry)
            elif hasattr(entry, 'type') and entry.type == 'event':
                if not (hasattr(entry, 'is_initiating_event') and entry.is_initiating_event):
                    subsequent_events.append(entry)
        
        # Build timeline text
        timeline_text = []
        for entry in timeline:
            if hasattr(entry, 'timestamp') and entry.timestamp:
                entry_type = entry.type.title() if hasattr(entry, 'type') else ''
                description = entry.description if hasattr(entry, 'description') else ''
                timeline_text.append(f"- {entry.timestamp}: {entry_type} - {description}")
        
        # Build initiating event text
        initiating_event_text = "None identified"
        if initiating_events:
            initiating_event_text = "\n".join([
                f"- {entry.timestamp}: {entry.description}"
                for entry in initiating_events
                if hasattr(entry, 'timestamp') and hasattr(entry, 'description')
            ])
        
        # Build subsequent events text
        subsequent_events_text = "None"
        if subsequent_events:
            subsequent_events_text = "\n".join([
                f"- {entry.timestamp}: {entry.description}"
                for entry in subsequent_events
                if hasattr(entry, 'timestamp') and hasattr(entry, 'description')
            ])
        
        # Build evidence text
        evidence_text = []
        for ev in evidence:
            ev_type = ev.type if hasattr(ev, 'type') else 'Document'
            ev_desc = ev.description if hasattr(ev, 'description') else ev.get('description', '') if isinstance(ev, dict) else ''
            evidence_text.append(f"- {ev_type}: {ev_desc}")
        
        return f"""
Using USCG causal analysis methodology per MCI-O3B procedures, identify causal factors from this timeline and evidence.

CRITICAL USCG REQUIREMENTS:
1. For the INITIATING EVENT (first adverse outcome): Identify causal factors across ALL categories (organization, workplace, precondition, production, defense)
2. For SUBSEQUENT EVENTS: Focus ONLY on DEFENSE factors that failed to prevent progression from the initiating event

INITIATING EVENT (First adverse outcome):
{initiating_event_text}

SUBSEQUENT EVENTS (Events that followed the initiating event):
{subsequent_events_text}

FULL TIMELINE:
{chr(10).join(timeline_text) if timeline_text else 'No timeline available'}

EVIDENCE:
{chr(10).join(evidence_text) if evidence_text else 'No evidence available'}

Causal factor titles MUST be written in the negative form:
- "Failure of..." (e.g., "Failure of crew to follow safety procedures")
- "Inadequate..." (e.g., "Inadequate oversight by management")
- "Lack of..." (e.g., "Lack of proper safety equipment")
- "Absence of..." (e.g., "Absence of effective communication")
- "Insufficient..." (e.g., "Insufficient training provided")

Categories:
- Organization: Management decisions, policies, culture
- Workplace: Physical environment, equipment, procedures
- Precondition: Individual factors, team factors, environmental factors
- Production: Unsafe acts, errors, violations
- Defense: Barriers that failed or were absent

Please identify causal factors in JSON format following USCG methodology:
[
  {{
    "category": "organization|workplace|precondition|production|defense",
    "title": "Failure of... / Inadequate... / Lack of... / Absence of... / Insufficient...",
    "description": "Detailed description of the causal factor (1-2 sentences describing what went wrong)",
    "evidence_support": ["references to supporting evidence"],
    "analysis": "In-depth analysis (3-5 paragraphs) that includes: 1) The specific conditions that led to this factor, 2) How this factor directly contributed to the incident, 3) The chain of events it caused or enabled, 4) Why existing safeguards failed to prevent it, 5) References to specific findings of fact. IMPORTANT: Make reasonable assumptions about maritime operations, crew behavior, and vessel conditions that are highly probable based on the evidence. State assumptions clearly (e.g., 'It is likely that...', 'Based on standard practice...', 'This suggests that...')",
    "event_type": "initiating|subsequent",
    "related_event": "description of the specific event this factor relates to"
  }}
]

CRITICAL REQUIREMENTS:
1. Title MUST be a short phrase (5-10 words max) in negative form
2. Analysis MUST be comprehensive (3-5 paragraphs minimum) and reference specific evidence
3. Each factor must clearly link cause to effect
4. Initiating event gets ALL category types, subsequent events get ONLY defense factors
5. **IDENTIFY MULTIPLE FACTORS**: A comprehensive causal analysis typically requires 3-7 causal factors minimum across different categories. Look for factors in:
   - Organization (management decisions, policies)
   - Workplace (equipment, procedures, environment)
   - Precondition (crew factors, conditions)
   - Production (unsafe acts, errors)
   - Defense (failed barriers, absent safeguards)
6. Make reasonable assumptions about:
   - Standard maritime procedures that should have been followed
   - Typical crew training and qualifications
   - Normal vessel maintenance practices
   - Common safety equipment and systems
   - Weather and sea conditions if not specified
   - Communication protocols and chain of command
7. State assumptions clearly using phrases like:
   - "Based on standard maritime practice..."
   - "It is reasonable to assume that..."
   - "This suggests that..."
   - "Typically in such situations..."
   - "Industry standards would require..."

**IMPORTANT**: Return a JSON array with MULTIPLE causal factors. A single factor is rarely sufficient for a complete USCG causal analysis.
"""
# Anthropic AI Assistant for ROI generation
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
from dotenv import load_dotenv

from src.models.roi_models import (
    InvestigationProject, TimelineEntry, CausalFactor, 
    Evidence, Finding, AnalysisSection
)

# Load environment variables
load_dotenv()

class AnthropicAssistant:
    """Anthropic AI Assistant specifically for ROI document generation"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Anthropic client with API key from environment"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            print("🟡 Anthropic Assistant initialized successfully")
        else:
            print("❌ Warning: ANTHROPIC_API_KEY not found in environment variables")
    
    def generate_complete_roi_sections(self, project: InvestigationProject) -> Dict[str, Any]:
        """Generate complete ROI sections using Anthropic Claude"""
        if not self.client:
            return {}
        
        prompt = self._create_complete_roi_prompt(project)
        
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.3,
                system="You are an expert USCG marine casualty investigator with 20+ years experience writing Reports of Investigation. You produce professional, concise documents that match the style of actual USCG investigation reports. Your writing is clear, factual, and follows the exact format of USCG ROI documents. You avoid verbose technical language and focus on concise, professional narrative.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return self._parse_roi_sections(message.content[0].text)
            
        except Exception as e:
            print(f"Error generating ROI sections with Anthropic: {e}")
            return {}
    
    def generate_findings_of_fact_from_timeline(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> List[str]:
        """Generate professional findings of fact using Anthropic"""
        print("🟡 Anthropic: generate_findings_of_fact_from_timeline called")
        if not self.client:
            print("❌ Anthropic: No client available, returning empty list")
            return []
        
        prompt = self._create_findings_generation_prompt(timeline, evidence)
        
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.2,
                system="You are a senior USCG investigator writing findings of fact for a Report of Investigation. Write concise, professional findings that establish the factual foundation. Match the style of actual USCG investigation reports - clear, factual, and properly numbered.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return self._parse_findings_statements(message.content[0].text)
            
        except Exception as e:
            print(f"Error generating findings with Anthropic: {e}")
            return []
    
    def generate_background_findings_from_evidence(self, evidence_library: List[Evidence], incident_date) -> List[str]:
        """Generate background/supporting findings from evidence for Section 4.2"""
        if not self.client:
            return []
        
        # Prepare evidence summary
        evidence_summary = []
        for evidence in evidence_library[:10]:  # Limit to avoid token limits
            evidence_summary.append(f"- {evidence.filename} ({evidence.type}): {evidence.description}")
        
        prompt = f"""
Generate professional USCG Findings of Fact for Section 4.2 (Supporting Information) based on available evidence.

INCIDENT DATE: {incident_date.strftime('%B %d, %Y') if incident_date else 'Unknown'}

AVAILABLE EVIDENCE:
{chr(10).join(evidence_summary)}

Generate 3-5 supporting findings that provide:
1. Vessel condition and maintenance history
2. Crew qualifications and experience
3. Weather and environmental conditions
4. Regulatory compliance status
5. Previous inspections or incidents

DO NOT repeat incident-day events. Focus on BACKGROUND context.

STYLE EXAMPLES for 4.2:
- "The vessel's Certificate of Inspection was current and valid through December 31, 2023."
- "Maintenance records indicate the main engine underwent major overhaul in March 2023."
- "The captain held a valid 100-ton Master license with 15 years of experience in local waters."
- "Weather reports for the week prior showed a developing low-pressure system."

Provide findings as clean statements without numbering (numbering will be added later).
Return as a JSON array of strings.
"""
        
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return self._parse_findings_statements(message.content[0].text)
            
        except Exception as e:
            print(f"Error generating background findings with Anthropic: {e}")
            return []
    
    def improve_analysis_text(self, factor: CausalFactor) -> str:
        """Generate concise, professional analysis text for a causal factor"""
        print("🟡 Anthropic: improve_analysis_text called")
        if not self.client:
            print("❌ Anthropic: No client available, using fallback")
            return factor.analysis_text or factor.description
        
        prompt = f"""
Write a concise professional analysis for this causal factor in a USCG Report of Investigation.

CAUSAL FACTOR:
Title: {factor.title}
Category: {factor.category}
Description: {factor.description}
Current Analysis: {factor.analysis_text or 'None provided'}

REQUIREMENTS:
1. Write 2-3 concise sentences maximum
2. Use "It is reasonable to believe..." phrasing when appropriate
3. Focus on HOW this factor contributed to the casualty
4. Avoid technical jargon and verbose explanations
5. Match the professional style of actual USCG reports

STYLE EXAMPLES FROM TARGET FORMAT:
- "It is reasonable to believe that the lack of formal safety training contributed to the crew's inability to respond effectively to the emergency."
- "The absence of proper maintenance records suggests that critical equipment failures went undetected."
- "Limited operational experience in local waters was a direct factor in the navigation error."

Provide ONLY the improved analysis text, no other commentary.
"""
        
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=300,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            print(f"Error improving analysis with Anthropic: {e}")
            return factor.analysis_text or factor.description
    
    def _create_complete_roi_prompt(self, project: InvestigationProject) -> str:
        """Create comprehensive prompt for full ROI generation"""
        # Gather project data
        vessel_info = []
        for vessel in project.vessels:
            vessel_info.append(f"- {vessel.official_name} (O.N. {vessel.identification_number})")
        
        timeline_text = []
        for entry in sorted(project.timeline, key=lambda x: x.timestamp or datetime.min)[:20]:
            if entry.timestamp:
                timeline_text.append(f"- {entry.timestamp.strftime('%B %d, %Y at %H%M')}: {entry.description}")
        
        causal_factors_text = []
        for factor in project.causal_factors:
            causal_factors_text.append(f"- {factor.category.upper()}: {factor.title}")
        
        return f"""
Generate professional USCG Report of Investigation sections based on this incident data. Match the concise, professional style of actual USCG reports.

INCIDENT INFORMATION:
Type: {project.incident_info.incident_type}
Location: {project.incident_info.location}
Date: {project.incident_info.incident_date.strftime('%B %d, %Y') if project.incident_info.incident_date else 'Unknown'}
Vessels: {', '.join(vessel_info)}

KEY TIMELINE EVENTS:
{chr(10).join(timeline_text)}

IDENTIFIED CAUSAL FACTORS:
{chr(10).join(causal_factors_text)}

Generate the following ROI sections in JSON format:

1. EXECUTIVE SUMMARY (3 paragraphs):
   - Paragraph 1: Scene setting - what activity was taking place
   - Paragraph 2: Outcomes - what happened as a result
   - Paragraph 3: Causal factors determination

2. KEY FINDINGS OF FACT (10-15 numbered statements):
   - Professional factual statements from the timeline
   - Properly numbered (4.1.1, 4.1.2, etc.)
   - Include times, dates, specific details

3. CONCLUSIONS (3-5 numbered statements):
   - Concise determination of cause
   - Focus on initiating event and key factors

4. ACTIONS TAKEN (2-3 specific actions):
   - Post-casualty testing
   - Safety orders issued
   - Industry notifications

5. RECOMMENDATIONS (3-5 concise items):
   - Specific safety improvements
   - Training enhancements
   - Equipment upgrades

STYLE REQUIREMENTS:
- Be concise and professional
- Avoid verbose technical language
- Use active voice where appropriate
- Match actual USCG report style
- Focus on facts over procedural language

Provide response as JSON:
{{
  "executive_summary": {{
    "scene_setting": "paragraph text",
    "outcomes": "paragraph text",
    "causal_factors": "paragraph text"
  }},
  "findings_of_fact": ["4.1.1. Finding one", "4.1.2. Finding two", ...],
  "conclusions": ["6.1.1. Conclusion one", "6.1.2. Conclusion two", ...],
  "actions_taken": ["7.1. Action one", "7.2. Action two", ...],
  "recommendations": ["8.1.1. Recommendation one", "8.1.2. Recommendation two", ...]
}}
"""
    
    def _create_findings_generation_prompt(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> str:
        """Create prompt for findings generation"""
        # Identify incident date from initiating event
        incident_date = None
        for entry in timeline:
            if hasattr(entry, 'is_initiating_event') and entry.is_initiating_event and entry.timestamp:
                incident_date = entry.timestamp.date()
                break
        
        # Separate timeline into incident-day and background entries
        incident_entries = []
        background_entries = []
        
        for entry in sorted(timeline, key=lambda x: x.timestamp or datetime.min):
            if entry.timestamp:
                if incident_date and entry.timestamp.date() == incident_date:
                    incident_entries.append(entry)
                else:
                    background_entries.append(entry)
        
        # Format entries
        incident_text = []
        for entry in incident_entries:
            time_str = entry.timestamp.strftime('%B %d, %Y, at %H%M')
            incident_text.append(f"- {time_str}: {entry.type.upper()} - {entry.description}")
        
        background_text = []
        for entry in background_entries[:5]:  # Limit background entries
            time_str = entry.timestamp.strftime('%B %d, %Y')
            background_text.append(f"- {time_str}: {entry.description}")
        
        return f"""
Convert this timeline into professional USCG Findings of Fact for Section 4.1 of a Report of Investigation.

FOCUS: Section 4.1 should focus on the INCIDENT DAY events - the actual casualty sequence and immediate circumstances.
Background information and pre-incident conditions will be handled separately in Section 4.2.

INCIDENT DAY EVENTS (Primary focus for 4.1):
{chr(10).join(incident_text) if incident_text else "No incident-day events identified"}

BACKGROUND/PRE-INCIDENT INFORMATION (Save for 4.2):
{chr(10).join(background_text) if background_text else "No background events"}

Write 8-12 numbered findings (4.1.1, 4.1.2, etc.) focusing on:
1. The incident sequence itself
2. Immediate circumstances on the day of the casualty
3. Direct causal events and conditions
4. Critical timeline points during the incident
5. Emergency response actions taken

DO NOT include background information, vessel history, crew qualifications, or pre-incident conditions in 4.1.

STYLE EXAMPLE for 4.1 (Incident Focus):
4.1.1. On August 1, 2023, at 0500, the commercial fishing vessel LEGACY departed Morehead City, North Carolina, for routine fishing operations.
4.1.2. At 1430, while operating in 6-foot seas, the vessel experienced a sudden loss of propulsion.
4.1.3. The engineer reported flooding in the engine room through a failed shaft seal at 1435.
4.1.4. The captain issued a distress call on VHF Channel 16 at 1442.

Provide findings as a JSON array of strings.
"""
    
    def _parse_roi_sections(self, response_text: str) -> Dict[str, Any]:
        """Parse ROI sections from Anthropic response"""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except Exception as e:
            print(f"Error parsing ROI sections: {e}")
        
        return {
            "executive_summary": {
                "scene_setting": "",
                "outcomes": "",
                "causal_factors": ""
            },
            "findings_of_fact": [],
            "conclusions": [],
            "actions_taken": [],
            "recommendations": []
        }
    
    def _parse_findings_statements(self, response_text: str) -> List[str]:
        """Parse findings statements from response"""
        try:
            # Try JSON array first
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        
        # Fallback to line parsing
        findings = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and '4.1.' in line:
                findings.append(line)
        
        return findings if findings else []
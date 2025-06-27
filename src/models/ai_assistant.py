# AI Assistant integration for IOAgent using OpenAI API

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

from src.models.roi_models import (
    InvestigationProject, TimelineEntry, CausalFactor, 
    Evidence, Finding, AnalysisSection
)

# Load environment variables
load_dotenv()

class AIAssistant:
    """AI Assistant for ROI generation using OpenAI API"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key from environment"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            print("Warning: OPENAI_API_KEY not found in environment variables")
    
    def suggest_timeline_entries(self, evidence_text: str, existing_timeline: List[Any]) -> List[Dict[str, Any]]:
        """Suggest timeline entries based on evidence text"""
        if not self.client:
            return []
        
        prompt = self._create_timeline_suggestion_prompt(evidence_text, existing_timeline)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-mini-2025-01-31",
                messages=[
                    {"role": "system", "content": "You are an expert USCG marine casualty investigator."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response and return suggestions
            suggestions = self._parse_timeline_suggestions(response.choices[0].message.content)
            return suggestions
            
        except Exception as e:
            print(f"Error getting timeline suggestions: {e}")
            return []
    
    def identify_causal_factors(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> List[Dict[str, Any]]:
        """Identify potential causal factors from timeline and evidence"""
        if not self.client:
            return []
        
        prompt = self._create_causal_analysis_prompt(timeline, evidence)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are an expert in USCG causal analysis methodology using the Swiss Cheese model. You have extensive experience in maritime operations, vessel safety systems, and human factors in marine casualties. When analyzing incidents, you make reasonable and probable assumptions based on standard maritime practices, typical crew behaviors, and common vessel configurations. You clearly state these assumptions in your analysis while maintaining professional objectivity."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            factors = self._parse_causal_factors(response.choices[0].message.content)
            return factors
            
        except Exception as e:
            print(f"Error identifying causal factors: {e}")
            return []
    
    def chat(self, prompt: str, model: str = "o3-2025-04-16") -> str:
        """Generate a simple chat completion using the specified OpenAI chat model.

        Args:
            prompt (str): The user prompt to send to the model.
            model (str, optional): The OpenAI model to use. Defaults to "o3-2025-04-16".

        Returns:
            str: The model's response content.

        Raises:
            ValueError: If the OpenAI client is not initialized.
            RuntimeError: If the OpenAI API call fails.
        """
        if not self.client:
            raise ValueError("OpenAI client is not initialized")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
    
    def generate_findings_of_fact_from_timeline(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> List[str]:
        """Generate professional findings of fact statements from timeline entries"""
        if not self.client:
            return []
        
        prompt = self._create_findings_generation_prompt(timeline, evidence)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are an expert USCG marine casualty investigator with extensive experience writing professional Reports of Investigation. You excel at converting timeline data into polished, professional findings of fact that meet USCG standards and read like expert investigative reports."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            findings = self._parse_findings_statements(response.choices[0].message.content)
            return findings
            
        except Exception as e:
            print(f"Error generating findings of fact: {e}")
            return []

    def improve_analysis_text(self, analysis_text: str, supporting_findings: List[Finding]) -> str:
        """Improve analysis section text"""
        if not self.client:
            return analysis_text
        
        prompt = self._create_analysis_improvement_prompt(analysis_text, supporting_findings)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer specializing in USCG investigation reports."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error improving analysis text: {e}")
            return analysis_text
    
    def generate_executive_summary(self, project: InvestigationProject) -> Dict[str, str]:
        """Generate executive summary paragraphs"""
        if not self.client:
            return {"scene_setting": "", "outcomes": "", "causal_factors": ""}
        
        prompt = self._create_executive_summary_prompt(project)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are an expert USCG investigator writing executive summaries."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = self._parse_executive_summary(response.choices[0].message.content)
            return summary
            
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            return {"scene_setting": "", "outcomes": "", "causal_factors": ""}
    
    def check_consistency(self, project: InvestigationProject) -> List[Dict[str, str]]:
        """Check consistency across ROI sections"""
        if not self.client:
            return []
        
        prompt = self._create_consistency_check_prompt(project)
        
        try:
            response = self.client.chat.completions.create(
                model="o3-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are a quality assurance expert for USCG investigation reports."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            issues = self._parse_consistency_issues(response.choices[0].message.content)
            return issues
            
        except Exception as e:
            print(f"Error checking consistency: {e}")
            return []
    
    def _create_timeline_suggestion_prompt(self, evidence_text: str, existing_timeline: List[Any]) -> str:
        """Create prompt for timeline suggestions"""
        existing_entries = "\n".join([
            f"- {entry.get('timestamp', entry.timestamp if hasattr(entry, 'timestamp') else '')}: "
            f"{entry.get('type', entry.type if hasattr(entry, 'type') else '').title()} - "
            f"{entry.get('description', entry.description if hasattr(entry, 'description') else '')}"
            for entry in existing_timeline 
            if (hasattr(entry, 'timestamp') and entry.timestamp) or (isinstance(entry, dict) and entry.get('timestamp'))
        ])
        
        return f"""
Based on the following evidence text, suggest timeline entries for a USCG marine casualty investigation.

IMPORTANT CLASSIFICATION RULES:
- Action: Something performed solely by an individual (e.g., "Captain ordered full astern", "Engineer started pump")
- Condition: The state of a person, place, or thing at a specific time (e.g., "Visibility was 0.5 miles", "Engine room was flooding")
- Event: An adverse outcome that requires causal factor analysis (e.g., "Vessel collided with pier", "Fire broke out in engine room")

Look for specific timestamps, dates, and times mentioned in the text. Extract key facts that describe:
1. What people did (Actions)
2. Environmental or equipment states (Conditions)
3. Adverse outcomes or incidents (Events)

Evidence text:
{evidence_text}

Existing timeline entries:
{existing_entries}

Please suggest new timeline entries in JSON format. Include specific timestamps when mentioned in the text:
[
  {{
    "timestamp": "YYYY-MM-DD HH:MM",
    "type": "action|condition|event",
    "description": "Clear, factual description of what happened",
    "confidence": "high|medium|low",
    "assumptions": ["any assumptions made if timestamp or details are inferred"],
    "personnel_involved": ["names or roles of people involved if mentioned"]
  }}
]
"""
    
    def _create_causal_analysis_prompt(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> str:
        """Create prompt for causal factor identification"""
        # Separate initiating event from subsequent events
        initiating_events = [entry for entry in timeline if hasattr(entry, 'is_initiating_event') and entry.is_initiating_event]
        subsequent_events = [entry for entry in timeline if entry.type == 'event' and not (hasattr(entry, 'is_initiating_event') and entry.is_initiating_event)]
        
        timeline_text = "\n".join([
            f"- {entry.timestamp}: {entry.type.title()} - {entry.description}"
            for entry in timeline if entry.timestamp
        ])
        
        initiating_event_text = "None identified" if not initiating_events else "\n".join([
            f"- {entry.timestamp}: {entry.description}"
            for entry in initiating_events
        ])
        
        subsequent_events_text = "None" if not subsequent_events else "\n".join([
            f"- {entry.timestamp}: {entry.description}"
            for entry in subsequent_events
        ])
        
        evidence_text = "\n".join([
            f"- {ev.type}: {ev.description}"
            for ev in evidence
        ])
        
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
{timeline_text}

EVIDENCE:
{evidence_text}

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
5. Make reasonable assumptions about:
   - Standard maritime procedures that should have been followed
   - Typical crew training and qualifications
   - Normal vessel maintenance practices
   - Common safety equipment and systems
   - Weather and sea conditions if not specified
   - Communication protocols and chain of command
6. State assumptions clearly using phrases like:
   - "Based on standard maritime practice..."
   - "It is reasonable to assume that..."
   - "This suggests that..."
   - "Typically in such situations..."
   - "Industry standards would require..."
"""
    
    def _create_findings_generation_prompt(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> str:
        """Create prompt for generating professional findings of fact from timeline"""
        timeline_text = "\n".join([
            f"- {entry.timestamp.strftime('%B %d, %Y, at %H%M') if entry.timestamp else 'Time unknown'}: {entry.type.title()} - {entry.description}"
            for entry in sorted(timeline, key=lambda x: x.timestamp or datetime.min)
        ])
        
        evidence_text = "\n".join([
            f"- {ev.type}: {ev.description} (Source: {ev.source})"
            for ev in evidence
        ])
        
        return f"""
Convert this timeline and evidence into professional USCG "Findings of Fact" statements for a Report of Investigation.

TIMELINE ENTRIES:
{timeline_text}

SUPPORTING EVIDENCE:
{evidence_text}

REQUIREMENTS:
1. Write as numbered statements (4.1.1, 4.1.2, etc.)
2. Use professional, objective language appropriate for legal documents
3. Include specific times, dates, locations, and measurements when available
4. Follow chronological order
5. Each statement should be a complete factual assertion supported by evidence
6. Use past tense throughout
7. Include vessel details, personnel information, and operational context
8. Write as coherent narrative, not bullet points
9. Ensure each finding can stand alone as a factual statement

STYLE EXAMPLES:
- "On August 1, 2023, at 0500, the commercial fishing vessel departed New Bedford, Massachusetts, with a crew of five for a planned 10-day fishing trip."
- "At 0530, the vessel cleared the harbor and set course southeast toward fishing grounds approximately 200 nautical miles from port."
- "Weather conditions at the time of departure included light winds from the southwest at 5-10 knots and calm seas."

Please provide the findings of fact as a JSON array of strings:
["4.1.1. [First finding statement]", "4.1.2. [Second finding statement]", ...]

Focus on creating professional, detailed findings that establish the factual foundation for the investigation.
"""
    
    def _create_analysis_improvement_prompt(self, analysis_text: str, supporting_findings: List[Finding]) -> str:
        """Create prompt for improving analysis text"""
        findings_text = "\n".join([
            f"- {finding.statement}"
            for finding in supporting_findings
        ])
        
        return f"""
Improve the following analysis section for a USCG ROI report. The analysis should:
- Be written in past tense
- Link clearly to supporting findings of fact
- Explain how the causal factor contributed to the incident
- Use objective, professional language
- Follow USCG writing standards

Current analysis text:
{analysis_text}

Supporting findings of fact:
{findings_text}

Please provide an improved version of the analysis text.
"""
    
    def _create_executive_summary_prompt(self, project: InvestigationProject) -> str:
        """Create prompt for executive summary generation"""
        # Gather project information
        vessel_info = ", ".join([
            f"{v.official_name} ({v.identification_number})"
            for v in project.vessels if v.official_name
        ])
        
        timeline_summary = "\n".join([
            f"- {entry.description}"
            for entry in project.timeline[:10]  # First 10 entries
        ])
        
        causal_factors_summary = "\n".join([
            f"- {factor.title}: {factor.description}"
            for factor in project.causal_factors
        ])
        
        return f"""
Generate a three-paragraph executive summary for a USCG ROI report with the following structure:

Paragraph 1 (Scene Setting): Describe the maritime activity and what happened
Paragraph 2 (Outcomes): Summarize consequences (damage, casualties, etc.)
Paragraph 3 (Causal Factors): List events in sequence and causal factors

Project Information:
- Vessels: {vessel_info}
- Incident Type: {project.incident_info.incident_type}
- Location: {project.incident_info.location}
- Date: {project.incident_info.incident_date}

Key Timeline Events:
{timeline_summary}

Identified Causal Factors:
{causal_factors_summary}

Please provide the executive summary in JSON format:
{{
  "scene_setting": "Paragraph 1 text",
  "outcomes": "Paragraph 2 text", 
  "causal_factors": "Paragraph 3 text"
}}
"""
    
    def _create_consistency_check_prompt(self, project: InvestigationProject) -> str:
        """Create prompt for consistency checking"""
        return f"""
Review this USCG ROI project for consistency issues. Check that:
- Conclusions derive from analysis
- Analysis derives from findings of fact
- Timeline entries are supported by evidence
- Causal factors are properly linked
- No contradictions exist between sections

Project data summary:
- Timeline entries: {len(project.timeline)}
- Evidence items: {len(project.evidence_library)}
- Causal factors: {len(project.causal_factors)}
- Findings: {len(project.roi_document.findings_of_fact)}
- Analysis sections: {len(project.roi_document.analysis_sections)}
- Conclusions: {len(project.roi_document.conclusions)}

Please identify any consistency issues in JSON format:
[
  {{
    "type": "error|warning|info",
    "section": "section name",
    "description": "description of the issue",
    "suggestion": "suggested fix"
  }}
]
"""
    
    def _parse_timeline_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse timeline suggestions from AI response"""
        try:
            # Try to extract JSON from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        return []
    
    def _parse_findings_statements(self, response_text: str) -> List[str]:
        """Parse findings of fact statements from AI response"""
        try:
            # Try to extract JSON array from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        
        # Fallback: parse line by line
        findings = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('4.1.' in line or '4.2.' in line):
                # Remove any leading bullets or quotes
                line = line.strip('"\'•-*')
                findings.append(line)
        
        return findings if findings else ["4.1.1. Timeline data requires further development to generate findings."]
    
    def _parse_causal_factors(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse causal factors from AI response"""
        try:
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        return []
    
    def _parse_executive_summary(self, response_text: str) -> Dict[str, str]:
        """Parse executive summary from AI response"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        return {"scene_setting": "", "outcomes": "", "causal_factors": ""}
    
    def _parse_consistency_issues(self, response_text: str) -> List[Dict[str, str]]:
        """Parse consistency issues from AI response"""
        try:
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
        except:
            pass
        return []

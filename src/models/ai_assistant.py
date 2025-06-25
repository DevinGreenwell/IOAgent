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
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are an expert USCG marine casualty investigator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
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
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are an expert in USCG causal analysis methodology using the Swiss Cheese model."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            factors = self._parse_causal_factors(response.choices[0].message.content)
            return factors
            
        except Exception as e:
            print(f"Error identifying causal factors: {e}")
            return []
    
    def chat(self, prompt: str, model: str = "gpt-4.1-nano-2025-04-14") -> str:
        """Generate a simple chat completion using the specified OpenAI chat model.

        Args:
            prompt (str): The user prompt to send to the model.
            model (str, optional): The OpenAI model to use. Defaults to "gpt-4.1-nano-2025-04-14".

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
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")
    
    def improve_analysis_text(self, analysis_text: str, supporting_findings: List[Finding]) -> str:
        """Improve analysis section text"""
        if not self.client:
            return analysis_text
        
        prompt = self._create_analysis_improvement_prompt(analysis_text, supporting_findings)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are an expert technical writer specializing in USCG investigation reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
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
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are an expert USCG investigator writing executive summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
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
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are a quality assurance expert for USCG investigation reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
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
        timeline_text = "\n".join([
            f"- {entry.timestamp}: {entry.type.title()} - {entry.description}"
            for entry in timeline if entry.timestamp
        ])
        
        evidence_text = "\n".join([
            f"- {ev.type}: {ev.description}"
            for ev in evidence
        ])
        
        return f"""
Using USCG causal analysis methodology and the Swiss Cheese model, identify causal factors from this timeline and evidence.

CRITICAL REQUIREMENT: Causal factor titles MUST be written in the negative form using phrases like:
- "Failure of..." (e.g., "Failure of crew to follow safety procedures")
- "Inadequate..." (e.g., "Inadequate oversight by management")
- "Lack of..." (e.g., "Lack of proper safety equipment")
- "Absence of..." (e.g., "Absence of effective communication")
- "Insufficient..." (e.g., "Insufficient training provided")

Causal factors should be categorized as:
- Organization: Management decisions, policies, culture
- Workplace: Physical environment, equipment, procedures
- Precondition: Individual factors, team factors, environmental factors
- Production: Unsafe acts, errors, violations
- Defense: Barriers that failed or were absent

Timeline:
{timeline_text}

Evidence:
{evidence_text}

Please identify causal factors in JSON format with NEGATIVE titles:
[
  {{
    "category": "organization|workplace|precondition|production|defense",
    "title": "Failure of... / Inadequate... / Lack of... / Absence of... / Insufficient...",
    "description": "Detailed description of the causal factor",
    "evidence_support": ["references to supporting evidence"],
    "analysis": "How this factor contributed to the incident"
  }}
]
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

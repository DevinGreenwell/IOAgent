# Anthropic AI Assistant for ROI generation
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
import re

# Short two‑sentence exemplar to anchor Claude’s style
STYLE_SNIPPET = (
    "COMMERCIAL FISHING VESSEL LEGACY (O.N. 530648), CREWMEMBER DEATH "
    "NEAR WARREN CHANNEL, ALASKA ON 01 AUGUST 2023\n\n"
    "On 01 August 2023, at approximately 0615 local time, the commercial fishing vessel "
    "LEGACY was engaged in seine‑fishing operations near Point Warde when the seine skiff "
    "grounded on a rock outcrop, ejecting the operator into the water."
)
from src.models.roi_models import (
    InvestigationProject, TimelineEntry, CausalFactor, 
    Evidence, Finding, AnalysisSection
)

class AnthropicAssistant:
    """Anthropic AI Assistant specifically for ROI document generation"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
        # Use fixed Anthropic model (hard‑coded)
        self.model_name = "claude-sonnet-4-20250514"
    
    def _initialize_client(self):
        """Initialize Anthropic client with API key from environment"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        import logging
        logger = logging.getLogger('app')
        
        logger.info(f"ANTHROPIC INIT: API key available: {api_key is not None}")
        if api_key:
            logger.info(f"ANTHROPIC INIT: API key starts with: {api_key[:20]}...")
        
        if api_key:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info("🟡 Anthropic Assistant initialized successfully")
            except Exception as e:
                logger.error(f"ANTHROPIC INIT: Failed to initialize client: {e}")
                self.client = None
        else:
            logger.error("❌ ANTHROPIC INIT: API key not found in environment variables")
            self.client = None
    
    def generate_complete_roi_sections(self, project: InvestigationProject) -> Dict[str, Any]:
        """Generate complete ROI sections using Anthropic Claude"""
        if not self.client:
            return {}
        
        prompt = self._create_complete_roi_prompt(project)
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
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
                model=self.model_name,
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
                model=self.model_name,
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
EXEMPLAR (mirror headings, tone, and numbering):
{STYLE_SNIPPET}

---
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
        try:
            return self._safe_json_extract(response_text)
        except ValueError as err:
            print(f"Error parsing ROI sections: {err}")
            return {
                "executive_summary": {"scene_setting": "", "outcomes": "", "causal_factors": ""},
                "findings_of_fact": [], "conclusions": [], "actions_taken": [], "recommendations": []
            }

    def _safe_json_extract(self, text: str):
        """
        Return the first valid JSON object or array found in `text`.
        Raises ValueError if none is found.
        """
        try:
            candidate = re.search(r'(\{.*\}|\[.*\])', text, re.S).group(1)
            return json.loads(candidate)
        except Exception as exc:
            raise ValueError("No valid JSON found") from exc

    def _parse_findings_statements(self, response_text: str) -> List[str]:
        try:
            data = self._safe_json_extract(response_text)
            # Expecting a JSON array; coerce to list of strings
            if isinstance(data, list):
                return [str(item) for item in data]
        except ValueError:
            # fallback: extract lines containing '4.1.'
            pass
        
        findings = [ln.strip() for ln in response_text.splitlines() if '4.1.' in ln]
        return findings

    def suggest_timeline_entries(self, evidence_text: str, existing_timeline: List[Any]) -> List[Dict[str, Any]]:
        """Suggest timeline entries based on evidence text using Anthropic"""
        import logging
        logger = logging.getLogger('app')
        
        logger.info("ANTHROPIC: suggest_timeline_entries called")
        
        if not self.client:
            logger.warning("ANTHROPIC: No client available, attempting to reinitialize...")
            self._initialize_client()
            
        if not self.client:
            logger.error("ANTHROPIC: Client initialization failed, cannot proceed")
            return []
        
        logger.info(f"ANTHROPIC: Evidence text length: {len(evidence_text)}")
        logger.info(f"ANTHROPIC: Existing timeline entries: {len(existing_timeline)}")
        
        prompt = self._create_timeline_suggestion_prompt(evidence_text, existing_timeline)
        
        try:
            logger.info("ANTHROPIC: Sending request to Anthropic API")
            logger.info(f"ANTHROPIC: Using model: {self.model_name}")
            logger.info(f"ANTHROPIC: Prompt length: {len(prompt)}")
            
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=3000,
                temperature=0.2,
                system="You are a senior USCG marine casualty investigator with 20+ years of experience conducting formal investigations under 46 CFR Part 4. You excel at comprehensive document analysis and timeline reconstruction from complex investigation materials. You understand that timeline entries become the foundation for Findings of Fact in Reports of Investigation, so your extraction must be meticulous, complete, and evidence-based. You have extensive knowledge of maritime operations, vessel systems, crew procedures, and emergency response protocols.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            logger.info("ANTHROPIC: Received response from Anthropic API")
            
            # Log the raw response for debugging
            raw_response = message.content[0].text
            logger.info(f"ANTHROPIC: Raw response (first 500 chars): {raw_response[:500]}")
            
            # Parse response and return suggestions
            suggestions = self._parse_timeline_suggestions(raw_response)
            logger.info(f"ANTHROPIC: Parsed suggestions: {suggestions}")
            logger.info(f"ANTHROPIC: Final result: {len(suggestions)} suggestions")
            return suggestions
            
        except Exception as e:
            print(f"Error getting timeline suggestions: {e}")
            import traceback
            traceback.print_exc()
            return []

    def identify_causal_factors(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> List[Dict[str, Any]]:
        """Identify potential causal factors from timeline and evidence using Anthropic"""
        if not self.client:
            return []
        
        prompt = self._create_causal_analysis_prompt(timeline, evidence)
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=0.2,
                system="You are an expert in USCG causal analysis methodology using the Swiss Cheese model. You have extensive experience in maritime operations, vessel safety systems, and human factors in marine casualties. When analyzing incidents, you make reasonable and probable assumptions based on standard maritime practices, typical crew behaviors, and common vessel configurations. You clearly state these assumptions in your analysis while maintaining professional objectivity.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            factors = self._parse_causal_factors(message.content[0].text)
            return factors
            
        except Exception as e:
            print(f"Error identifying causal factors: {e}")
            return []

    def chat(self, prompt: str, model: str = None) -> str:
        """Generate a simple chat completion using Anthropic"""
        if not self.client:
            raise ValueError("Anthropic client is not initialized")

        try:
            message = self.client.messages.create(
                model=model or self.model_name,
                max_tokens=1500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {e}")

    def generate_findings_from_evidence_content(self, evidence_content: str, evidence_filename: str) -> List[str]:
        """Generate findings of fact directly from evidence content using Anthropic"""
        if not self.client:
            return []
        
        prompt = self._create_evidence_findings_prompt(evidence_content, evidence_filename)
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=0.2,
                system="You are an expert USCG marine casualty investigator with extensive experience writing professional Reports of Investigation. You excel at analyzing evidence documents and extracting factual findings that meet USCG standards and read like expert investigative reports.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            findings = self._parse_findings_statements(message.content[0].text)
            return findings
            
        except Exception as e:
            print(f"Error generating findings from evidence content: {e}")
            return []

    def generate_executive_summary(self, project) -> Dict[str, str]:
        """Generate executive summary paragraphs using Anthropic"""
        if not self.client:
            return {"scene_setting": "", "outcomes": "", "causal_factors": ""}
        
        prompt = self._create_executive_summary_prompt(project)
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=1500,
                temperature=0.2,
                system="You are an expert USCG investigator writing executive summaries.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = self._parse_executive_summary(message.content[0].text)
            return summary
            
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            return {"scene_setting": "", "outcomes": "", "causal_factors": ""}

    def check_consistency(self, project) -> List[Dict[str, str]]:
        """Check consistency across ROI sections using Anthropic"""
        if not self.client:
            return []
        
        prompt = self._create_consistency_check_prompt(project)
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=1500,
                temperature=0.2,
                system="You are a quality assurance expert for USCG investigation reports.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            issues = self._parse_consistency_issues(message.content[0].text)
            return issues
            
        except Exception as e:
            print(f"Error checking consistency: {e}")
            return []

    def _create_timeline_suggestion_prompt(self, evidence_text: str, existing_timeline: List[Any]) -> str:
        """Create comprehensive timeline extraction prompt matching ROI methodology"""
        existing_entries = "\n".join([
            f"- {entry.get('timestamp', entry.timestamp if hasattr(entry, 'timestamp') else '')}: "
            f"{entry.get('type', entry.type if hasattr(entry, 'type') else '').title()} - "
            f"{entry.get('description', entry.description if hasattr(entry, 'description') else '')}"
            for entry in existing_timeline 
            if (hasattr(entry, 'timestamp') and entry.timestamp) or (isinstance(entry, dict) and entry.get('timestamp'))
        ])
        
        return f"""Extract timeline entries from this marine casualty investigation document. Look for:

1. ACTIONS: Crew decisions, equipment operations, communications
2. CONDITIONS: Weather, vessel status, personnel factors  
3. EVENTS: Incidents, failures, casualties

DOCUMENT CONTENT:
{evidence_text[:10000] if len(evidence_text) > 10000 else evidence_text}

EXISTING TIMELINE (avoid duplicates):
{existing_entries}

Return a JSON array of timeline entries found. Each entry should have:
- timestamp: Date/time (YYYY-MM-DD HH:MM format)
- type: "action", "condition", or "event" 
- description: Factual description from document
- confidence: "high", "medium", or "low"

Example format:
[
  {{
    "timestamp": "2023-08-01 05:00",
    "type": "action", 
    "description": "Vessel departed port for fishing operations",
    "confidence": "high"
  }}
]

Return ONLY the JSON array, no other text."""

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
Using USCG causal analysis methodology per MCI-O3B procedures, identify causal factors from this timeline and evidence.

FULL TIMELINE:
{timeline_text}

EVIDENCE:
{evidence_text}

Please identify causal factors in JSON format following USCG methodology:
[
  {{
    "category": "organization|workplace|precondition|production|defense",
    "title": "Brief title describing the causal factor",
    "description": "Detailed description of the causal factor",
    "evidence_support": ["references to supporting evidence"],
    "analysis": "In-depth analysis of how this factor contributed to the incident"
  }}
]
"""

    def _create_evidence_findings_prompt(self, evidence_content: str, evidence_filename: str) -> str:
        """Create prompt for generating findings of fact directly from evidence content"""
        return f"""
Analyze this evidence document and extract professional USCG "Findings of Fact" statements for a Report of Investigation.

EVIDENCE DOCUMENT: {evidence_filename}

DOCUMENT CONTENT:
{evidence_content[:15000] if len(evidence_content) > 15000 else evidence_content}

Generate professional findings of fact as numbered statements. Focus on factual information, not analysis or conclusions.

Please provide the findings of fact as a JSON array of strings:
["4.1.1. [First finding statement]", "4.1.2. [Second finding statement]", ...]
"""

    def _create_executive_summary_prompt(self, project) -> str:
        """Create prompt for executive summary generation"""
        return f"""
Generate a three-paragraph executive summary for a USCG ROI report with the following structure:

Paragraph 1 (Scene Setting): Describe the maritime activity and what happened
Paragraph 2 (Outcomes): Summarize consequences (damage, casualties, etc.)
Paragraph 3 (Causal Factors): List events in sequence and causal factors

Please provide the executive summary in JSON format:
{{
  "scene_setting": "Paragraph 1 text",
  "outcomes": "Paragraph 2 text", 
  "causal_factors": "Paragraph 3 text"
}}
"""

    def _create_consistency_check_prompt(self, project) -> str:
        """Create prompt for consistency checking"""
        return f"""
Review this USCG ROI project for consistency issues. Check that:
- Conclusions derive from analysis
- Analysis derives from findings of fact
- Timeline entries are supported by evidence
- Causal factors are properly linked
- No contradictions exist between sections

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
        try:
            result = self._safe_json_extract(response_text)
            print(f"DEBUG: Successfully parsed JSON: {len(result) if isinstance(result, list) else 'not a list'} items")
            return result
        except Exception as err:
            print(f"DEBUG: JSON parsing failed: {err}")
            print(f"DEBUG: Response text that failed to parse: {response_text[:200]}...")
            
            # Also log to application logger
            import logging
            logging.getLogger('app').error(f"JSON PARSING FAILED: {err}")
            logging.getLogger('app').error(f"FAILED RESPONSE TEXT: {response_text[:200]}...")
            
            return [{"error": "ParseError", "task": "timeline", "message": str(err), "description": "Failed to parse AI response"}]

    def _parse_causal_factors(self, response_text: str) -> List[Dict[str, Any]]:
        try:
            data = self._safe_json_extract(response_text)
            return data if isinstance(data, list) else []
        except Exception as err:
            return [{"error": "ParseError", "task": "causal", "message": str(err)}]

    def _parse_executive_summary(self, response_text: str) -> Dict[str, str]:
        try:
            return self._safe_json_extract(response_text)
        except Exception as err:
            return {"error": f"ParseError summary – {err}"}

    def _parse_consistency_issues(self, response_text: str) -> List[Dict[str, str]]:
        try:
            data = self._safe_json_extract(response_text)
            return data if isinstance(data, list) else []
        except Exception as err:
            return [{"error": "ParseError", "task": "consistency", "message": str(err)}]
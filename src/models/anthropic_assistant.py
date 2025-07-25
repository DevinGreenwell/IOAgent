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
                system="You are a senior USCG investigator writing findings of fact for a Report of Investigation. Your goal is to write professional findings that establish the factual foundation. Match the style of actual USCG investigation reports - clear, factual, and properly numbered.",
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
                temperature=0.4,
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
Write a professional analysis for this causal factor in a USCG Report of Investigation.

CAUSAL FACTOR:
Title: {factor.title}
Category: {factor.category}
Description: {factor.description}
Current Analysis: {factor.analysis_text or 'None provided'}

REQUIREMENTS:
1. Write 3-5 concise sentences maximum
2. Use "It is reasonable to believe..." phrasing when appropriate
3. Focus on HOW this factor contributed to the casualty
4. Avoid technical jargon and verbose explanations
5. Match the professional style of actual USCG reports

STYLE EXAMPLES FROM TARGET FORMAT:
- "It is reasonable to believe that the lack of formal safety training contributed to the crew's inability to respond effectively to the emergency."
- "The absence of proper maintenance records suggests that critical equipment failures went undetected."
- "Limited operational experience in local waters was likely a factor in the navigation error."

Provide ONLY the improved analysis text, no other commentary.
"""
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=400,
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
        """Create comprehensive prompt for full ROI generation."""
        from src.models.ai_prompt_builder import AIPromptBuilder
        return AIPromptBuilder.build_complete_roi_prompt(project)

    
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
        
        style_example = ("STYLE EXAMPLE for 4.1 (Incident Focus):\n"
                        "* On August 1, 2023, at 05:00, the commercial fishing vessel LEGACY departed Morehead City, North Carolina, for routine fishing operations.\n"
                        "* At 14:30, while operating in 6-foot seas, the vessel experienced a sudden loss of propulsion.\n"
                        "* The engineer reported flooding in the engine room through a failed shaft seal at 14:35.\n"
                        "* The captain issued a distress call on VHF Channel 16 at 14:42.")
        
        prompt_text = f"""Convert this timeline into professional USCG Findings of Fact for Section 4.1 of a Report of Investigation.

FOCUS: Section 4.1 should focus on the INCIDENT DAY events - it should tell the story ofthe actual casualty sequence and immediate circumstances.
Background information, pre-incident conditions, and vessel or personnel history will be handled separately in Section 4.2.

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

{style_example}

Provide findings as a JSON array of strings."""
        return prompt_text
    
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
        Handles markdown code blocks and other formatting.
        Raises ValueError if none is found.
        """
        import logging
        logger = logging.getLogger('app')
        
        # First, try to strip markdown code blocks if present
        original_text = text
        if '```json' in text:
            # Extract content between ```json and ```
            match = re.search(r'```json\s*\n(.*?)(?:\n```|$)', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
                logger.info("🟡 JSON EXTRACT: Stripped markdown code blocks (json)")
                logger.debug(f"Extracted text: {text[:100]}...")
        elif '```' in text:
            # Generic code block without language specifier
            match = re.search(r'```\s*\n(.*?)(?:\n```|$)', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
                logger.info("🟡 JSON EXTRACT: Stripped generic code blocks")
        
        # Also handle case where the text starts with ```json without capturing it
        if text.startswith('```json'):
            text = text[7:].strip()
            if text.endswith('```'):
                text = text[:-3].strip()
            logger.info("🟡 JSON EXTRACT: Stripped markdown markers directly")
        
        try:
            # Try to parse the whole text as JSON first
            result = json.loads(text.strip())
            logger.info(f"🟢 JSON EXTRACT: Successfully parsed JSON (type: {type(result)}, length: {len(result) if isinstance(result, list) else 'n/a'})")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON EXTRACT: Direct parse failed: {e}")
            
            # If that fails, try to find JSON object/array
            try:
                # More aggressive search - find first [ or { and last ] or }
                start_idx = -1
                end_idx = -1
                
                # Find start of JSON
                for i, char in enumerate(text):
                    if char in '[{':
                        start_idx = i
                        break
                
                # Find end of JSON (matching bracket)
                if start_idx >= 0:
                    bracket_count = 0
                    start_char = text[start_idx]
                    end_char = ']' if start_char == '[' else '}'
                    
                    for i in range(start_idx, len(text)):
                        if text[i] == start_char:
                            bracket_count += 1
                        elif text[i] == end_char:
                            bracket_count -= 1
                            if bracket_count == 0:
                                end_idx = i
                                break
                    
                    if end_idx > start_idx:
                        json_text = text[start_idx:end_idx + 1]
                        result = json.loads(json_text)
                        logger.info(f"🟢 JSON EXTRACT: Extracted JSON via bracket matching (type: {type(result)})")
                        return result
                    else:
                        # Handle truncated JSON by trying to repair it
                        logger.warning("⚠️ JSON EXTRACT: Attempting to repair truncated JSON")
                        repaired_json = self._repair_truncated_json(text[start_idx:])
                        if repaired_json:
                            logger.info(f"🟢 JSON EXTRACT: Successfully repaired truncated JSON")
                            return repaired_json
                
                # Final fallback - regex
                candidate = re.search(r'(\{.*\}|\[.*\])', text, re.S).group(1)
                result = json.loads(candidate)
                logger.info(f"🟢 JSON EXTRACT: Extracted JSON via regex (type: {type(result)})")
                return result
            except Exception as exc:
                logger.error(f"🔴 JSON EXTRACT: All extraction attempts failed")
                logger.error(f"🔴 JSON EXTRACT: Original text: {original_text[:500]}...")
                logger.error(f"🔴 JSON EXTRACT: After stripping: {text[:500]}...")
                
                # Last attempt for partial JSON - try to reconstruct if we can identify structure
                try:
                    logger.warning("🟡 JSON EXTRACT: Attempting emergency reconstruction")
                    reconstructed = self._emergency_json_reconstruction(text)
                    if reconstructed:
                        logger.info("🟢 JSON EXTRACT: Emergency reconstruction successful")
                        return reconstructed
                except Exception as repair_exc:
                    logger.error(f"🔴 JSON EXTRACT: Emergency reconstruction failed: {repair_exc}")
                
                raise ValueError("No valid JSON found") from exc
    
    def _repair_truncated_json(self, json_text: str) -> List[Dict[str, Any]]:
        """Attempt to repair truncated JSON by finding complete entries"""
        import logging
        logger = logging.getLogger('app')
        
        try:
            # Find all complete JSON objects in the truncated text
            complete_objects = []
            current_object = ""
            brace_count = 0
            in_string = False
            escape_next = False
            
            for char in json_text:
                if escape_next:
                    escape_next = False
                    current_object += char
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    current_object += char
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                current_object += char
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and current_object.strip().startswith('{'):
                            # We have a complete object
                            try:
                                obj = json.loads(current_object.strip())
                                complete_objects.append(obj)
                                current_object = ""
                            except json.JSONDecodeError:
                                # Skip malformed objects
                                current_object = ""
            
            if complete_objects:
                logger.info(f"🟢 JSON REPAIR: Recovered {len(complete_objects)} complete timeline entries")
                return complete_objects
            else:
                logger.warning("⚠️ JSON REPAIR: No complete objects found")
                return []
                
        except Exception as e:
            logger.error(f"🔴 JSON REPAIR: Failed to repair JSON: {e}")
            return []

    def _emergency_json_reconstruction(self, text: str) -> Dict[str, Any]:
        """Emergency reconstruction of JSON from partial or malformed response"""
        import logging
        logger = logging.getLogger('app')
        
        try:
            # Look for common ROI JSON patterns and try to fix
            logger.info("🟡 EMERGENCY JSON: Analyzing text for ROI structure")
            
            # If we see "executive_summary" but no opening brace, add it
            if '"executive_summary"' in text and not text.strip().startswith('{'):
                logger.info("🟡 EMERGENCY JSON: Adding missing opening brace")
                text = '{' + text
            
            # If we see incomplete JSON but can identify sections, try to build minimal structure
            if '"executive_summary"' in text or '"incident_summary"' in text:
                logger.info("🟡 EMERGENCY JSON: Building minimal ROI structure")
                
                # Extract whatever executive summary we can find
                exec_match = re.search(r'"executive_summary":\s*\{[^}]*"scene_setting":\s*"([^"]*)"', text, re.DOTALL)
                scene_setting = exec_match.group(1) if exec_match else "Unable to determine incident details from available evidence."
                
                # Build minimal valid structure
                minimal_roi = {
                    "incident_summary": {
                        "date": "Unknown",
                        "time": "Unknown", 
                        "location": "Unknown",
                        "vessel_name": "Unknown",
                        "incident_type": "Marine Casualty",
                        "description": "Incident details extracted from evidence files"
                    },
                    "executive_summary": {
                        "scene_setting": scene_setting,
                        "outcomes": "Investigation is ongoing. Additional analysis required.",
                        "causal_factors": "Causal factors to be determined through further analysis."
                    },
                    "vessel_information": {
                        "official_name": "To be determined",
                        "official_number": "To be determined",
                        "specifications": "To be determined from evidence",
                        "ownership": "To be determined",
                        "equipment": "To be determined"
                    },
                    "personnel_casualties": [],
                    "findings_of_fact": [
                        "4.1.1. Evidence files were uploaded for analysis.",
                        "4.1.2. Investigation is ongoing.",
                        "4.1.3. Additional findings to be determined through detailed analysis."
                    ],
                    "causal_factors": [
                        {
                            "title": "To be determined through detailed analysis",
                            "category": "organization",
                            "description": "Causal analysis pending",
                            "analysis": "Detailed analysis required"
                        }
                    ],
                    "conclusions": {
                        "initiating_event": "The initiating event is under investigation.",
                        "causal_determinations": ["Analysis pending"],
                        "violations": "None identified at this time",
                        "other_conclusions": "Investigation ongoing"
                    },
                    "actions_taken": [
                        "7.1. Coast Guard investigation initiated under 46 CFR Part 4."
                    ],
                    "recommendations": {
                        "safety_recommendations": [
                            "8.1.1. Complete detailed analysis of all evidence files."
                        ],
                        "administrative_recommendations": []
                    }
                }
                
                logger.info("🟢 EMERGENCY JSON: Created minimal ROI structure")
                return minimal_roi
            
            return None
            
        except Exception as e:
            logger.error(f"🔴 EMERGENCY JSON: Reconstruction failed: {e}")
            return None

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
                max_tokens=4000,  # Increased for detailed timeline extraction
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
        import logging
        logger = logging.getLogger('app')
        
        if not self.client:
            logger.error("🔴 CAUSAL: No Anthropic client available")
            return []
        
        prompt = self._create_causal_analysis_prompt(timeline, evidence)
        logger.info(f"🟡 CAUSAL: Sending prompt to AI (length: {len(prompt)})")
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=3000,  # Increased for multiple factors
                temperature=0.2,
                system="You are an expert in USCG causal analysis methodology using the Swiss Cheese model. You have extensive experience in maritime operations, vessel safety systems, and human factors in marine casualties. When analyzing incidents, you make reasonable and probable assumptions based on standard maritime practices, typical crew behaviors, and common vessel configurations. You clearly state these assumptions in your analysis while maintaining professional objectivity. IMPORTANT: You should identify MULTIPLE causal factors across different categories - typically 3-7 factors minimum for a comprehensive analysis.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            raw_response = message.content[0].text
            logger.info(f"🟡 CAUSAL: AI response length: {len(raw_response)}")
            logger.info(f"🟡 CAUSAL: AI response preview: {raw_response[:500]}")
            
            factors = self._parse_causal_factors(raw_response)
            logger.info(f"🟢 CAUSAL: Parsed {len(factors)} factors from AI response")
            
            if len(factors) < 2:
                logger.warning(f"⚠️ CAUSAL: Only {len(factors)} factors identified - this may be insufficient for comprehensive analysis")
            
            return factors
            
        except Exception as e:
            logger.error(f"🔴 CAUSAL: Error identifying causal factors: {e}")
            return []

    def chat(self, prompt: str, model: str = None) -> str:
        """Generate a simple chat completion using Anthropic"""
        if not self.client:
            raise ValueError("Anthropic client is not initialized")

        try:
            message = self.client.messages.create(
                model=model or self.model_name,
                max_tokens=4000,
                temperature=0.1,
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
        
        # Log the prompt being sent to debug data quality issues
        import logging
        logger = logging.getLogger('app')
        logger.info(f"🟡 EXEC SUMMARY: Generating summary with {len(project.timeline)} timeline entries, {len(project.causal_factors)} causal factors")
        logger.info(f"🟡 EXEC SUMMARY: Vessel info: {[v.official_name for v in project.vessels]}")
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=1500,  # Reduced to ensure concise output
                temperature=0.1,  # Much lower for factual, consistent tone
                system="You are a USCG marine casualty investigator writing official executive summaries. Your writing must be factual, professional, and concise - matching the style of actual USCG Reports of Investigation. Avoid colorful language, dramatic descriptions, or journalistic flourishes. Write clear, direct prose using standard maritime terminology. Each paragraph should be 4-5 sentences that convey essential facts without unnecessary elaboration.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            raw_response = message.content[0].text
            logger.info(f"🟡 EXEC SUMMARY: Raw AI response length: {len(raw_response)}")
            logger.info(f"🟡 EXEC SUMMARY: Response preview: {raw_response[:300]}")
            
            summary = self._parse_executive_summary(raw_response)
            
            # Validate summary quality
            for section, content in summary.items():
                if content and not content.startswith('error'):
                    sentence_count = len([s for s in content.split('.') if s.strip()])
                    if sentence_count < 3:
                        logger.warning(f"⚠️ EXEC SUMMARY: {section} only has {sentence_count} sentences (should be 4-6)")
            
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

    def _create_timeline_suggestion_prompt(self, evidence_text: str, existing_timeline: List[Any], filename: str = "") -> str:
        """Create comprehensive timeline extraction prompt matching ROI methodology."""
        from src.models.ai_prompt_builder import AIPromptBuilder
        return AIPromptBuilder.build_timeline_suggestion_prompt(evidence_text, filename, existing_timeline)

    def _create_causal_analysis_prompt(self, timeline: List[TimelineEntry], evidence: List[Evidence]) -> str:
        """Create prompt for causal factor identification with proper USCG methodology."""
        from src.models.ai_prompt_builder import AIPromptBuilder
        return AIPromptBuilder.build_causal_analysis_prompt(timeline, evidence)

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
        """Create comprehensive prompt for executive summary generation"""
        # Gather detailed project information
        vessel_info = []
        for vessel in project.vessels:
            vessel_info.append(f"{vessel.official_name} (O.N. {vessel.identification_number})")
        
        timeline_summary = []
        for entry in sorted(project.timeline, key=lambda x: x.timestamp or datetime.min)[:15]:
            if entry.timestamp:
                timeline_summary.append(f"- {entry.timestamp.strftime('%B %d, %Y at %H%M')}: {entry.description}")
        
        causal_factors_summary = []
        for factor in project.causal_factors:
            causal_factors_summary.append(f"- {factor.title}: {factor.description}")
        
        personnel_info = []
        for person in project.personnel:
            if person.role and person.status:
                personnel_info.append(f"- {person.role}: {person.status}")
        
        return f"""
You are writing a professional executive summary for a USCG Report of Investigation. This is NOT a brief summary - each paragraph must be 4-6 FULL, DETAILED sentences that create a compelling narrative.

Write exactly 3 paragraphs, each 4-5 sentences. Use factual, professional language like actual USCG reports. Avoid overly detailed or colorful descriptions.

PROJECT INFORMATION:
- Vessels: {', '.join(vessel_info) if vessel_info else 'Not specified'}
- Incident Type: {project.incident_info.incident_type or 'Marine casualty'}
- Location: {project.incident_info.location or 'Not specified'}
- Date: {project.incident_info.incident_date.strftime('%B %d, %Y') if project.incident_info.incident_date else 'Not specified'}
- Personnel: {chr(10).join(personnel_info) if personnel_info else 'Not specified'}

DETAILED TIMELINE:
{chr(10).join(timeline_summary) if timeline_summary else 'No timeline entries available'}

IDENTIFIED CAUSAL FACTORS:
{chr(10).join(causal_factors_summary) if causal_factors_summary else 'No causal factors identified'}

REQUIREMENTS FOR EACH PARAGRAPH:

PARAGRAPH 1 - SCENE SETTING (4-5 sentences):
- State date, time, vessel name, and location of operations
- Describe what the vessel and crew were doing (fishing, transit, etc.)
- Note relevant operational details and conditions
- Describe the initiating incident clearly and factually

PARAGRAPH 2 - RESPONSE AND OUTCOMES (4-5 sentences):
- Describe immediate crew response and rescue efforts
- Note arrival of emergency responders or assistance
- State medical treatment provided and transport
- Give final casualty outcome (deceased, injured, etc.)

PARAGRAPH 3 - INVESTIGATION DETERMINATION (4-5 sentences):
- Start with: "Through its investigation, the Coast Guard determined that the initiating event for this casualty was [specific event]."
- Follow with: "Causal factors that contributed to this casualty include:"
- List factors as: "(1) [factor], (2) [factor], (3) [factor], and (4) [factor]."
- Use actual factor titles from the causal analysis, written concisely

WRITING REQUIREMENTS:
- Write in a factual, professional tone matching official USCG reports
- Each paragraph must be 4-5 complete sentences
- Avoid dramatic or colorful language
- Use standard maritime terminology
- Be concise - the entire summary must fit on one page
- Focus on essential facts only

Please provide the executive summary in JSON format:
{{
  "scene_setting": "[Paragraph 1 - Scene setting and incident]",
  "outcomes": "[Paragraph 2 - Response and outcomes]", 
  "causal_factors": "[Paragraph 3 - Investigation determination with numbered factors]"
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
        import logging
        logger = logging.getLogger('app')
        
        try:
            data = self._safe_json_extract(response_text)
            logger.info(f"🟡 CAUSAL PARSE: Extracted JSON type: {type(data)}")
            
            if isinstance(data, list):
                logger.info(f"🟢 CAUSAL PARSE: Successfully parsed {len(data)} factors")
                return data
            else:
                logger.warning(f"⚠️ CAUSAL PARSE: Expected list, got {type(data)}")
                return []
                
        except Exception as err:
            logger.error(f"🔴 CAUSAL PARSE: JSON parsing failed: {err}")
            logger.error(f"🔴 CAUSAL PARSE: Response text (first 1000 chars): {response_text[:1000]}")
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
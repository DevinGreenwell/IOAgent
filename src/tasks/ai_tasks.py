"""AI-powered async tasks for analysis and suggestions."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.celery_app import celery_app
from src.models.project import Project
from src.models.evidence import Evidence
from src.models.timeline_entry import TimelineEntry
from src.models.causal_factor import CausalFactor
from src.models.user import db
from src.services.anthropic_assistant import AnthropicAssistant

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def analyze_evidence_async(self, evidence_id: int) -> Dict[str, Any]:
    """
    Analyze evidence content using AI to extract key information.
    
    Args:
        evidence_id: ID of the evidence to analyze
    
    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(f"Starting AI analysis of evidence {evidence_id}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Loading evidence...'})
        
        with celery_app.app.app_context():
            evidence = Evidence.query.get(evidence_id)
            if not evidence:
                raise ValueError(f"Evidence {evidence_id} not found")
            
            if not evidence.content:
                raise ValueError("Evidence has no extracted content to analyze")
            
            self.update_state(state='PROGRESS', meta={'status': 'Analyzing content...'})
            
            # Initialize AI assistant
            ai_assistant = AnthropicAssistant()
            
            # Analyze evidence content
            analysis = ai_assistant.analyze_evidence(
                content=evidence.content,
                evidence_type=evidence.file_type,
                context={
                    'project_id': evidence.project_id,
                    'title': evidence.title,
                    'file_name': evidence.file_name
                }
            )
            
            # Update evidence with analysis results
            evidence.summary = analysis.get('summary', evidence.summary)
            if not evidence.metadata:
                evidence.metadata = {}
            evidence.metadata['ai_analysis'] = {
                'key_points': analysis.get('key_points', []),
                'entities': analysis.get('entities', []),
                'dates': analysis.get('dates', []),
                'locations': analysis.get('locations', []),
                'relevance_score': analysis.get('relevance_score', 0),
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            db.session.commit()
            
            logger.info(f"AI analysis completed for evidence {evidence_id}")
            
            return {
                'status': 'success',
                'evidence_id': evidence_id,
                'analysis': analysis,
                'message': 'Evidence analyzed successfully'
            }
            
    except Exception as e:
        logger.error(f"Error analyzing evidence {evidence_id}: {str(e)}")
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True, max_retries=3)
def generate_timeline_suggestions_async(self, project_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate timeline event suggestions based on project context.
    
    Args:
        project_id: ID of the project
        context: Additional context for generation
    
    Returns:
        Dictionary with suggested timeline events
    """
    try:
        logger.info(f"Generating timeline suggestions for project {project_id}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Analyzing project data...'})
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get existing timeline and evidence
            existing_timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                                  .order_by(TimelineEntry.timestamp).all()
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            
            self.update_state(state='PROGRESS', meta={'status': 'Generating suggestions...'})
            
            # Initialize AI assistant
            ai_assistant = AnthropicAssistant()
            
            # Generate suggestions
            suggestions = ai_assistant.suggest_timeline_events(
                project=project,
                existing_timeline=existing_timeline,
                evidence=evidence,
                focus_area=context.get('focus_area'),
                time_range=context.get('time_range')
            )
            
            # Format suggestions
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    'timestamp': suggestion.get('timestamp'),
                    'description': suggestion.get('description'),
                    'event_type': suggestion.get('event_type', 'observation'),
                    'significance': suggestion.get('significance', 'medium'),
                    'rationale': suggestion.get('rationale', ''),
                    'evidence_support': suggestion.get('evidence_support', [])
                })
            
            logger.info(f"Generated {len(formatted_suggestions)} timeline suggestions for project {project_id}")
            
            return {
                'status': 'success',
                'project_id': project_id,
                'suggestions': formatted_suggestions,
                'message': f'Generated {len(formatted_suggestions)} timeline suggestions'
            }
            
    except Exception as e:
        logger.error(f"Error generating timeline suggestions for project {project_id}: {str(e)}")
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True, max_retries=3)
def analyze_causal_chain_async(self, project_id: int, incident_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform comprehensive causal chain analysis using Swiss Cheese model.
    
    Args:
        project_id: ID of the project
        incident_type: Type of incident for specialized analysis
    
    Returns:
        Dictionary with causal analysis results
    """
    try:
        logger.info(f"Starting causal chain analysis for project {project_id}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Loading project data...'})
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get all relevant data
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                         .order_by(TimelineEntry.timestamp).all()
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            existing_factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            self.update_state(state='PROGRESS', meta={'status': 'Analyzing causal chains...'})
            
            # Initialize AI assistant
            ai_assistant = AnthropicAssistant()
            
            # Perform causal analysis
            analysis = ai_assistant.analyze_causal_chain(
                project=project,
                timeline=timeline,
                evidence=evidence,
                existing_factors=existing_factors,
                incident_type=incident_type or project.incident_info.get('type') if project.incident_info else None
            )
            
            # Structure the analysis results
            results = {
                'primary_causes': analysis.get('primary_causes', []),
                'contributing_factors': analysis.get('contributing_factors', []),
                'barrier_failures': analysis.get('barrier_failures', []),
                'systemic_issues': analysis.get('systemic_issues', []),
                'recommendations': analysis.get('recommendations', []),
                'risk_assessment': analysis.get('risk_assessment', {}),
                'prevention_strategies': analysis.get('prevention_strategies', [])
            }
            
            # Store analysis results in project metadata
            if not project.metadata:
                project.metadata = {}
            project.metadata['causal_analysis'] = {
                'results': results,
                'analyzed_at': datetime.utcnow().isoformat(),
                'incident_type': incident_type
            }
            db.session.commit()
            
            logger.info(f"Causal chain analysis completed for project {project_id}")
            
            return {
                'status': 'success',
                'project_id': project_id,
                'analysis': results,
                'message': 'Causal chain analysis completed successfully'
            }
            
    except Exception as e:
        logger.error(f"Error in causal analysis for project {project_id}: {str(e)}")
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True)
def generate_investigation_questions_async(self, project_id: int) -> Dict[str, Any]:
    """
    Generate investigation questions based on current project state.
    
    Args:
        project_id: ID of the project
    
    Returns:
        Dictionary with suggested investigation questions
    """
    try:
        logger.info(f"Generating investigation questions for project {project_id}")
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get current investigation state
            evidence_count = Evidence.query.filter_by(project_id=project_id).count()
            timeline_count = TimelineEntry.query.filter_by(project_id=project_id).count()
            causal_count = CausalFactor.query.filter_by(project_id=project_id).count()
            
            # Get gaps in timeline
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                         .order_by(TimelineEntry.timestamp).all()
            
            # Initialize AI assistant
            ai_assistant = AnthropicAssistant()
            
            # Generate questions based on gaps
            questions = ai_assistant.generate_investigation_questions(
                project=project,
                timeline=timeline,
                evidence_count=evidence_count,
                causal_count=causal_count
            )
            
            # Categorize questions
            categorized_questions = {
                'critical': [],
                'important': [],
                'supplementary': []
            }
            
            for question in questions:
                priority = question.get('priority', 'supplementary')
                categorized_questions[priority].append({
                    'question': question.get('question'),
                    'rationale': question.get('rationale'),
                    'data_needed': question.get('data_needed', []),
                    'potential_sources': question.get('potential_sources', [])
                })
            
            return {
                'status': 'success',
                'project_id': project_id,
                'questions': categorized_questions,
                'statistics': {
                    'evidence_count': evidence_count,
                    'timeline_count': timeline_count,
                    'causal_count': causal_count
                },
                'message': f'Generated {len(questions)} investigation questions'
            }
            
    except Exception as e:
        logger.error(f"Error generating questions for project {project_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def validate_investigation_completeness_async(self, project_id: int) -> Dict[str, Any]:
    """
    Validate investigation completeness and identify gaps.
    
    Args:
        project_id: ID of the project
    
    Returns:
        Dictionary with completeness assessment
    """
    try:
        logger.info(f"Validating investigation completeness for project {project_id}")
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Gather all data
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                         .order_by(TimelineEntry.timestamp).all()
            causal_factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            # Initialize AI assistant
            ai_assistant = AnthropicAssistant()
            
            # Perform completeness check
            assessment = ai_assistant.assess_investigation_completeness(
                project=project,
                evidence=evidence,
                timeline=timeline,
                causal_factors=causal_factors
            )
            
            # Calculate completeness score
            completeness_score = assessment.get('overall_score', 0)
            
            # Structure results
            results = {
                'completeness_score': completeness_score,
                'complete': completeness_score >= 80,  # 80% threshold
                'sections': {
                    'evidence': assessment.get('evidence_assessment', {}),
                    'timeline': assessment.get('timeline_assessment', {}),
                    'causal_analysis': assessment.get('causal_assessment', {}),
                    'recommendations': assessment.get('recommendations_assessment', {})
                },
                'gaps': assessment.get('identified_gaps', []),
                'suggestions': assessment.get('improvement_suggestions', []),
                'strengths': assessment.get('strengths', [])
            }
            
            return {
                'status': 'success',
                'project_id': project_id,
                'assessment': results,
                'message': f'Investigation is {completeness_score}% complete'
            }
            
    except Exception as e:
        logger.error(f"Error validating completeness for project {project_id}: {str(e)}")
        raise
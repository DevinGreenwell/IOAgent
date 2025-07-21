"""Document generation and processing tasks."""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.celery_app import celery_app
from src.models.project import Project
from src.models.evidence import Evidence
from src.models.timeline_entry import TimelineEntry
from src.models.causal_factor import CausalFactor
from src.models.generated_document import GeneratedDocument
from src.models.user import db
from src.services.anthropic_assistant import AnthropicAssistant
from src.services.document_generator import DocumentGenerator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_roi_async(self, project_id: int, user_id: int, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Report of Investigation asynchronously.
    
    Args:
        project_id: ID of the project
        user_id: ID of the requesting user
        options: Generation options (format, include_appendices, etc.)
    
    Returns:
        Dictionary with document information
    """
    try:
        logger.info(f"Starting ROI generation for project {project_id}")
        
        # Update task state
        self.update_state(state='PROGRESS', meta={'status': 'Loading project data...'})
        
        # Get project data
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Verify user has access
            if project.owner_id != user_id:
                raise ValueError("Unauthorized access to project")
            
            # Gather all project data
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                         .order_by(TimelineEntry.timestamp).all()
            causal_factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            self.update_state(state='PROGRESS', meta={'status': 'Generating document content...'})
            
            # Initialize services
            ai_assistant = AnthropicAssistant()
            doc_generator = DocumentGenerator()
            
            # Generate ROI content using AI
            roi_content = ai_assistant.generate_complete_roi(
                project=project,
                evidence=evidence,
                timeline=timeline,
                causal_factors=causal_factors,
                include_recommendations=options.get('include_recommendations', True)
            )
            
            self.update_state(state='PROGRESS', meta={'status': 'Creating document file...'})
            
            # Generate document
            file_format = options.get('format', 'docx')
            file_name = f"ROI_{project.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{file_format}"
            file_path = Path(celery_app.app.config['PROJECTS_FOLDER']) / str(project_id) / file_name
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create document
            if file_format == 'docx':
                doc_generator.create_docx_report(
                    content=roi_content,
                    file_path=str(file_path),
                    project=project,
                    include_appendices=options.get('include_appendices', False)
                )
            elif file_format == 'pdf':
                doc_generator.create_pdf_report(
                    content=roi_content,
                    file_path=str(file_path),
                    project=project
                )
            else:
                raise ValueError(f"Unsupported format: {file_format}")
            
            # Save document record
            document = GeneratedDocument(
                project_id=project_id,
                document_type='roi',
                file_name=file_name,
                file_path=str(file_path),
                metadata={
                    'format': file_format,
                    'options': options,
                    'generated_by': 'async_task',
                    'task_id': self.request.id
                }
            )
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"ROI generation completed for project {project_id}")
            
            return {
                'status': 'success',
                'document_id': document.id,
                'file_name': file_name,
                'file_path': str(file_path),
                'message': 'Report of Investigation generated successfully'
            }
            
    except Exception as e:
        logger.error(f"Error generating ROI for project {project_id}: {str(e)}")
        
        # Retry with exponential backoff
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True, max_retries=3)
def generate_summary_report_async(self, project_id: int, user_id: int) -> Dict[str, Any]:
    """
    Generate executive summary report asynchronously.
    
    Args:
        project_id: ID of the project
        user_id: ID of the requesting user
    
    Returns:
        Dictionary with document information
    """
    try:
        logger.info(f"Starting summary report generation for project {project_id}")
        
        self.update_state(state='PROGRESS', meta={'status': 'Generating summary...'})
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project or project.owner_id != user_id:
                raise ValueError("Project not found or unauthorized")
            
            # Gather data
            evidence_count = Evidence.query.filter_by(project_id=project_id).count()
            timeline_count = TimelineEntry.query.filter_by(project_id=project_id).count()
            causal_count = CausalFactor.query.filter_by(project_id=project_id).count()
            
            # Get key findings
            critical_events = TimelineEntry.query.filter_by(
                project_id=project_id,
                significance='critical'
            ).all()
            
            primary_causes = CausalFactor.query.filter_by(
                project_id=project_id
            ).filter(
                CausalFactor.category.in_(['Human Factors', 'Technical Factors'])
            ).all()
            
            # Create summary content
            summary = {
                'project_name': project.name,
                'description': project.description,
                'statistics': {
                    'evidence_files': evidence_count,
                    'timeline_events': timeline_count,
                    'causal_factors': causal_count
                },
                'key_findings': {
                    'critical_events': [
                        {
                            'timestamp': event.timestamp.isoformat(),
                            'description': event.description
                        } for event in critical_events[:5]
                    ],
                    'primary_causes': [
                        {
                            'category': cause.category,
                            'description': cause.description,
                            'remedial_action': cause.remedial_action
                        } for cause in primary_causes[:5]
                    ]
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Generate document
            doc_generator = DocumentGenerator()
            file_name = f"Summary_{project.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
            file_path = Path(celery_app.app.config['PROJECTS_FOLDER']) / str(project_id) / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            doc_generator.create_summary_document(summary, str(file_path))
            
            # Save document record
            document = GeneratedDocument(
                project_id=project_id,
                document_type='summary',
                file_name=file_name,
                file_path=str(file_path),
                metadata={
                    'task_id': self.request.id,
                    'statistics': summary['statistics']
                }
            )
            db.session.add(document)
            db.session.commit()
            
            return {
                'status': 'success',
                'document_id': document.id,
                'file_name': file_name,
                'message': 'Summary report generated successfully'
            }
            
    except Exception as e:
        logger.error(f"Error generating summary for project {project_id}: {str(e)}")
        retry_in = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True)
def export_project_data_async(self, project_id: int, user_id: int, format: str = 'json') -> Dict[str, Any]:
    """
    Export all project data in specified format.
    
    Args:
        project_id: ID of the project
        user_id: ID of the requesting user
        format: Export format (json, csv, xlsx)
    
    Returns:
        Dictionary with export file information
    """
    try:
        logger.info(f"Starting project data export for project {project_id} in {format} format")
        
        self.update_state(state='PROGRESS', meta={'status': 'Collecting project data...'})
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project or project.owner_id != user_id:
                raise ValueError("Project not found or unauthorized")
            
            # Collect all data
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                         .order_by(TimelineEntry.timestamp).all()
            causal_factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            self.update_state(state='PROGRESS', meta={'status': f'Exporting to {format}...'})
            
            # Export based on format
            exporter = DataExporter()
            file_name = f"Export_{project.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
            file_path = Path(celery_app.app.config['PROJECTS_FOLDER']) / str(project_id) / 'exports' / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                exporter.export_to_json(project, evidence, timeline, causal_factors, str(file_path))
            elif format == 'csv':
                exporter.export_to_csv(project, evidence, timeline, causal_factors, str(file_path))
            elif format == 'xlsx':
                exporter.export_to_excel(project, evidence, timeline, causal_factors, str(file_path))
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return {
                'status': 'success',
                'file_name': file_name,
                'file_path': str(file_path),
                'format': format,
                'message': f'Project data exported successfully to {format}'
            }
            
    except Exception as e:
        logger.error(f"Error exporting project {project_id}: {str(e)}")
        raise


class DataExporter:
    """Helper class for data export functionality."""
    
    def export_to_json(self, project, evidence, timeline, causal_factors, file_path):
        """Export project data to JSON format."""
        import json
        
        data = {
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'created_at': project.created_at.isoformat(),
                'vessel_info': project.vessel_info,
                'incident_info': project.incident_info
            },
            'evidence': [
                {
                    'id': e.id,
                    'title': e.title,
                    'file_name': e.file_name,
                    'summary': e.summary,
                    'uploaded_at': e.uploaded_at.isoformat()
                } for e in evidence
            ],
            'timeline': [
                {
                    'id': t.id,
                    'timestamp': t.timestamp.isoformat(),
                    'description': t.description,
                    'event_type': t.event_type,
                    'location': t.location,
                    'actors': t.actors,
                    'significance': t.significance
                } for t in timeline
            ],
            'causal_factors': [
                {
                    'id': c.id,
                    'category': c.category,
                    'description': c.description,
                    'barrier_type': c.barrier_type,
                    'remedial_action': c.remedial_action,
                    'contributing_factors': c.contributing_factors
                } for c in causal_factors
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_to_csv(self, project, evidence, timeline, causal_factors, file_path):
        """Export project data to CSV format (creates multiple files)."""
        import csv
        from pathlib import Path
        
        base_path = Path(file_path).parent
        base_name = Path(file_path).stem
        
        # Export timeline to CSV
        timeline_path = base_path / f"{base_name}_timeline.csv"
        with open(timeline_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'description', 'event_type', 
                'location', 'actors', 'significance'
            ])
            writer.writeheader()
            for t in timeline:
                writer.writerow({
                    'timestamp': t.timestamp.isoformat(),
                    'description': t.description,
                    'event_type': t.event_type,
                    'location': t.location,
                    'actors': t.actors,
                    'significance': t.significance
                })
        
        # Export causal factors to CSV
        causal_path = base_path / f"{base_name}_causal_factors.csv"
        with open(causal_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'category', 'description', 'barrier_type', 
                'remedial_action', 'contributing_factors'
            ])
            writer.writeheader()
            for c in causal_factors:
                writer.writerow({
                    'category': c.category,
                    'description': c.description,
                    'barrier_type': c.barrier_type,
                    'remedial_action': c.remedial_action,
                    'contributing_factors': ', '.join(c.contributing_factors or [])
                })
    
    def export_to_excel(self, project, evidence, timeline, causal_factors, file_path):
        """Export project data to Excel format."""
        try:
            import pandas as pd
            
            # Create Excel writer
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Project info
                project_df = pd.DataFrame([{
                    'Name': project.name,
                    'Description': project.description,
                    'Created': project.created_at,
                    'Vessel': project.vessel_info.get('name', 'N/A') if project.vessel_info else 'N/A',
                    'Incident Date': project.incident_info.get('date', 'N/A') if project.incident_info else 'N/A',
                    'Location': project.incident_info.get('location', 'N/A') if project.incident_info else 'N/A'
                }])
                project_df.to_excel(writer, sheet_name='Project Info', index=False)
                
                # Evidence
                evidence_df = pd.DataFrame([{
                    'Title': e.title,
                    'File Name': e.file_name,
                    'Summary': e.summary,
                    'Uploaded': e.uploaded_at
                } for e in evidence])
                evidence_df.to_excel(writer, sheet_name='Evidence', index=False)
                
                # Timeline
                timeline_df = pd.DataFrame([{
                    'Timestamp': t.timestamp,
                    'Description': t.description,
                    'Type': t.event_type,
                    'Location': t.location,
                    'Actors': t.actors,
                    'Significance': t.significance
                } for t in timeline])
                timeline_df.to_excel(writer, sheet_name='Timeline', index=False)
                
                # Causal factors
                causal_df = pd.DataFrame([{
                    'Category': c.category,
                    'Description': c.description,
                    'Barrier Type': c.barrier_type,
                    'Remedial Action': c.remedial_action,
                    'Contributing Factors': ', '.join(c.contributing_factors or [])
                } for c in causal_factors])
                causal_df.to_excel(writer, sheet_name='Causal Factors', index=False)
                
        except ImportError:
            # Fallback to CSV if pandas not available
            self.export_to_csv(project, evidence, timeline, causal_factors, file_path.replace('.xlsx', '.csv'))
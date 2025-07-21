"""Notification and communication async tasks."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.celery_app import celery_app
from src.models.user import User, db
from src.models.project import Project
from src.models.generated_document import GeneratedDocument

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_email_notification_async(self, user_id: int, subject: str, 
                                 body: str, template: Optional[str] = None) -> Dict[str, Any]:
    """
    Send email notification to user.
    
    Args:
        user_id: ID of the user to notify
        subject: Email subject
        body: Email body (plain text or HTML)
        template: Optional email template name
    
    Returns:
        Dictionary with send status
    """
    try:
        logger.info(f"Sending email notification to user {user_id}")
        
        with celery_app.app.app_context():
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if not user.email:
                raise ValueError(f"User {user_id} has no email address")
            
            # Get email configuration
            smtp_host = celery_app.app.config.get('SMTP_HOST', 'localhost')
            smtp_port = celery_app.app.config.get('SMTP_PORT', 587)
            smtp_user = celery_app.app.config.get('SMTP_USER')
            smtp_pass = celery_app.app.config.get('SMTP_PASS')
            from_email = celery_app.app.config.get('FROM_EMAIL', 'noreply@ioagent.app')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = user.email
            
            # Add body
            if template:
                # Render template (implementation would go here)
                html_body = body  # For now, use body as-is
                msg.attach(MIMEText(html_body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if smtp_user and smtp_pass:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {user.email}")
            
            return {
                'status': 'success',
                'user_id': user_id,
                'email': user.email,
                'subject': subject,
                'message': 'Email sent successfully'
            }
            
    except Exception as e:
        logger.error(f"Error sending email to user {user_id}: {str(e)}")
        retry_in = 2 ** self.request.retries * 60  # Exponential backoff in seconds
        raise self.retry(exc=e, countdown=retry_in)


@celery_app.task(bind=True)
def notify_document_ready_async(self, document_id: int) -> Dict[str, Any]:
    """
    Notify user when document generation is complete.
    
    Args:
        document_id: ID of the generated document
    
    Returns:
        Dictionary with notification status
    """
    try:
        logger.info(f"Sending document ready notification for document {document_id}")
        
        with celery_app.app.app_context():
            document = GeneratedDocument.query.get(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            project = Project.query.get(document.project_id)
            if not project:
                raise ValueError(f"Project {document.project_id} not found")
            
            user = User.query.get(project.owner_id)
            if not user:
                raise ValueError(f"User {project.owner_id} not found")
            
            # Prepare notification
            subject = f"Your {document.document_type.upper()} is ready - {project.name}"
            
            body = f"""
Dear {user.username},

Your {document.document_type} for the project "{project.name}" has been generated successfully.

Document Details:
- Type: {document.document_type.upper()}
- File: {document.file_name}
- Generated at: {document.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

You can download the document from your project dashboard.

Best regards,
IOAgent Team
            """
            
            # Send email notification
            send_email_notification_async.delay(user.id, subject, body)
            
            # Store in-app notification (if implemented)
            # create_in_app_notification(user.id, subject, body, document_id=document_id)
            
            return {
                'status': 'success',
                'document_id': document_id,
                'user_id': user.id,
                'message': 'Document ready notification sent'
            }
            
    except Exception as e:
        logger.error(f"Error sending document notification for document {document_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def notify_investigation_milestone_async(self, project_id: int, milestone: str) -> Dict[str, Any]:
    """
    Notify user of investigation milestones.
    
    Args:
        project_id: ID of the project
        milestone: Type of milestone reached
    
    Returns:
        Dictionary with notification status
    """
    try:
        logger.info(f"Sending milestone notification for project {project_id}: {milestone}")
        
        with celery_app.app.app_context():
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            user = User.query.get(project.owner_id)
            if not user:
                raise ValueError(f"User {project.owner_id} not found")
            
            # Define milestone messages
            milestone_messages = {
                'timeline_complete': {
                    'subject': 'Timeline Complete',
                    'body': 'Your investigation timeline is now complete with all critical events documented.'
                },
                'evidence_threshold': {
                    'subject': 'Evidence Collection Milestone',
                    'body': 'You have collected sufficient evidence for comprehensive analysis.'
                },
                'causal_analysis_ready': {
                    'subject': 'Ready for Causal Analysis',
                    'body': 'Your investigation has enough data for detailed causal analysis.'
                },
                'roi_ready': {
                    'subject': 'Ready to Generate ROI',
                    'body': 'Your investigation is complete enough to generate a Report of Investigation.'
                }
            }
            
            if milestone not in milestone_messages:
                raise ValueError(f"Unknown milestone: {milestone}")
            
            msg = milestone_messages[milestone]
            
            body = f"""
Dear {user.username},

Good news about your investigation "{project.name}"!

{msg['body']}

Next steps:
- Review your current data for completeness
- Consider generating reports or analysis
- Continue adding any missing information

Visit your project dashboard to continue.

Best regards,
IOAgent Team
            """
            
            # Send notification
            send_email_notification_async.delay(user.id, f"{msg['subject']} - {project.name}", body)
            
            # Update project metadata
            if not project.metadata:
                project.metadata = {}
            if 'milestones' not in project.metadata:
                project.metadata['milestones'] = {}
            project.metadata['milestones'][milestone] = datetime.utcnow().isoformat()
            db.session.commit()
            
            return {
                'status': 'success',
                'project_id': project_id,
                'milestone': milestone,
                'message': 'Milestone notification sent'
            }
            
    except Exception as e:
        logger.error(f"Error sending milestone notification for project {project_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def send_weekly_summary_async(self, user_id: int) -> Dict[str, Any]:
    """
    Send weekly investigation summary to user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        Dictionary with summary status
    """
    try:
        logger.info(f"Generating weekly summary for user {user_id}")
        
        with celery_app.app.app_context():
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get user's projects
            projects = Project.query.filter_by(owner_id=user_id).all()
            
            if not projects:
                return {
                    'status': 'skipped',
                    'user_id': user_id,
                    'message': 'No projects to summarize'
                }
            
            # Generate summary
            summary_lines = [
                f"Dear {user.username},",
                "",
                "Here's your weekly IOAgent investigation summary:",
                ""
            ]
            
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            for project in projects:
                # Get activity counts for the week
                from src.models.evidence import Evidence
                from src.models.timeline_entry import TimelineEntry
                from src.models.causal_factor import CausalFactor
                
                new_evidence = Evidence.query.filter(
                    Evidence.project_id == project.id,
                    Evidence.uploaded_at >= week_ago
                ).count()
                
                new_timeline = TimelineEntry.query.filter(
                    TimelineEntry.project_id == project.id,
                    TimelineEntry.created_at >= week_ago
                ).count()
                
                new_causal = CausalFactor.query.filter(
                    CausalFactor.project_id == project.id,
                    CausalFactor.created_at >= week_ago
                ).count()
                
                if new_evidence + new_timeline + new_causal > 0:
                    summary_lines.extend([
                        f"Project: {project.name}",
                        f"  - New evidence files: {new_evidence}",
                        f"  - New timeline events: {new_timeline}",
                        f"  - New causal factors: {new_causal}",
                        ""
                    ])
            
            summary_lines.extend([
                "Keep up the great investigation work!",
                "",
                "Best regards,",
                "IOAgent Team"
            ])
            
            # Send summary
            subject = "Your Weekly IOAgent Investigation Summary"
            body = "\n".join(summary_lines)
            
            send_email_notification_async.delay(user_id, subject, body)
            
            return {
                'status': 'success',
                'user_id': user_id,
                'projects_count': len(projects),
                'message': 'Weekly summary sent'
            }
            
    except Exception as e:
        logger.error(f"Error generating weekly summary for user {user_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def broadcast_system_announcement_async(self, subject: str, message: str, 
                                      user_filter: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Broadcast system announcement to users.
    
    Args:
        subject: Announcement subject
        message: Announcement message
        user_filter: Optional filter criteria for users
    
    Returns:
        Dictionary with broadcast status
    """
    try:
        logger.info(f"Broadcasting system announcement: {subject}")
        
        with celery_app.app.app_context():
            # Build user query
            query = User.query.filter_by(is_active=True)
            
            if user_filter:
                if 'role' in user_filter:
                    query = query.filter_by(role=user_filter['role'])
                if 'created_after' in user_filter:
                    query = query.filter(User.created_at >= user_filter['created_after'])
            
            users = query.all()
            
            if not users:
                return {
                    'status': 'skipped',
                    'message': 'No users match criteria',
                    'user_count': 0
                }
            
            # Queue notifications for each user
            sent_count = 0
            for user in users:
                try:
                    send_email_notification_async.delay(user.id, subject, message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to queue notification for user {user.id}: {str(e)}")
            
            return {
                'status': 'success',
                'user_count': len(users),
                'sent_count': sent_count,
                'message': f'Announcement queued for {sent_count} users'
            }
            
    except Exception as e:
        logger.error(f"Error broadcasting announcement: {str(e)}")
        raise
"""Maintenance and cleanup async tasks."""

import os
import logging
import shutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.celery_app import celery_app
from src.models.user import db
from src.models.project import Project
from src.models.evidence import Evidence
from src.models.generated_document import GeneratedDocument

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_old_files_async(self, days_old: int = 90) -> Dict[str, Any]:
    """
    Clean up old temporary and orphaned files.
    
    Args:
        days_old: Delete files older than this many days
    
    Returns:
        Dictionary with cleanup statistics
    """
    try:
        logger.info(f"Starting cleanup of files older than {days_old} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cleaned_files = 0
        freed_space = 0
        
        with celery_app.app.app_context():
            # Clean up orphaned evidence files
            evidence_records = Evidence.query.filter(Evidence.uploaded_at < cutoff_date).all()
            
            for evidence in evidence_records:
                file_path = Path(evidence.file_path)
                if file_path.exists():
                    # Check if evidence is still referenced
                    if not evidence.project:
                        # Orphaned evidence
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_files += 1
                            freed_space += file_size
                            
                            # Delete database record
                            db.session.delete(evidence)
                        except Exception as e:
                            logger.error(f"Error deleting file {file_path}: {str(e)}")
            
            # Clean up temporary files
            temp_dirs = [
                Path('static/uploads/temp'),
                Path('static/previews'),
                Path('static/thumbnails')
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    for file_path in temp_dir.iterdir():
                        if file_path.is_file():
                            file_stat = file_path.stat()
                            file_age = datetime.utcnow() - datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_age.days > days_old:
                                try:
                                    freed_space += file_stat.st_size
                                    file_path.unlink()
                                    cleaned_files += 1
                                except Exception as e:
                                    logger.error(f"Error deleting temp file {file_path}: {str(e)}")
            
            db.session.commit()
            
            logger.info(f"Cleanup completed: {cleaned_files} files deleted, {freed_space / 1024 / 1024:.2f} MB freed")
            
            return {
                'status': 'success',
                'cleaned_files': cleaned_files,
                'freed_space_mb': round(freed_space / 1024 / 1024, 2),
                'cutoff_date': cutoff_date.isoformat(),
                'message': f'Cleaned {cleaned_files} files, freed {freed_space / 1024 / 1024:.2f} MB'
            }
            
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        raise


@celery_app.task(bind=True)
def generate_usage_reports_async(self) -> Dict[str, Any]:
    """
    Generate usage reports for monitoring and analytics.
    
    Returns:
        Dictionary with report information
    """
    try:
        logger.info("Generating usage reports")
        
        with celery_app.app.app_context():
            # Gather statistics
            from src.models.user import User
            from src.models.timeline_entry import TimelineEntry
            from src.models.causal_factor import CausalFactor
            
            # Time ranges
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            # User statistics
            total_users = User.query.count()
            active_users_week = User.query.filter(User.last_login >= week_ago).count()
            active_users_month = User.query.filter(User.last_login >= month_ago).count()
            new_users_week = User.query.filter(User.created_at >= week_ago).count()
            
            # Project statistics
            total_projects = Project.query.count()
            active_projects_week = Project.query.filter(Project.updated_at >= week_ago).count()
            new_projects_week = Project.query.filter(Project.created_at >= week_ago).count()
            
            # Content statistics
            total_evidence = Evidence.query.count()
            new_evidence_week = Evidence.query.filter(Evidence.uploaded_at >= week_ago).count()
            total_timeline_entries = TimelineEntry.query.count()
            new_timeline_week = TimelineEntry.query.filter(TimelineEntry.created_at >= week_ago).count()
            total_causal_factors = CausalFactor.query.count()
            new_causal_week = CausalFactor.query.filter(CausalFactor.created_at >= week_ago).count()
            
            # Document generation statistics
            total_documents = GeneratedDocument.query.count()
            documents_week = GeneratedDocument.query.filter(GeneratedDocument.generated_at >= week_ago).count()
            
            # Storage statistics
            upload_folder = Path(celery_app.app.config.get('UPLOAD_FOLDER', 'static/uploads'))
            total_size = 0
            file_count = 0
            
            if upload_folder.exists():
                for path in upload_folder.rglob('*'):
                    if path.is_file():
                        total_size += path.stat().st_size
                        file_count += 1
            
            # Create report
            report = {
                'generated_at': now.isoformat(),
                'period': {
                    'start': week_ago.isoformat(),
                    'end': now.isoformat()
                },
                'users': {
                    'total': total_users,
                    'active_week': active_users_week,
                    'active_month': active_users_month,
                    'new_week': new_users_week
                },
                'projects': {
                    'total': total_projects,
                    'active_week': active_projects_week,
                    'new_week': new_projects_week
                },
                'content': {
                    'evidence': {
                        'total': total_evidence,
                        'new_week': new_evidence_week
                    },
                    'timeline_entries': {
                        'total': total_timeline_entries,
                        'new_week': new_timeline_week
                    },
                    'causal_factors': {
                        'total': total_causal_factors,
                        'new_week': new_causal_week
                    }
                },
                'documents': {
                    'total_generated': total_documents,
                    'generated_week': documents_week
                },
                'storage': {
                    'total_files': file_count,
                    'total_size_mb': round(total_size / 1024 / 1024, 2)
                }
            }
            
            # Save report
            reports_dir = Path('reports')
            reports_dir.mkdir(exist_ok=True)
            
            report_filename = f"usage_report_{now.strftime('%Y%m%d_%H%M%S')}.json"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Usage report generated: {report_path}")
            
            # Send summary to admins
            from src.tasks.notification_tasks import send_email_notification_async
            
            admin_users = User.query.filter_by(role='admin').all()
            for admin in admin_users:
                subject = f"IOAgent Weekly Usage Report - {now.strftime('%Y-%m-%d')}"
                body = f"""
Weekly Usage Report Summary:

Users:
- Total: {report['users']['total']}
- Active this week: {report['users']['active_week']}
- New this week: {report['users']['new_week']}

Projects:
- Total: {report['projects']['total']}
- Active this week: {report['projects']['active_week']}

Content Added This Week:
- Evidence files: {report['content']['evidence']['new_week']}
- Timeline entries: {report['content']['timeline_entries']['new_week']}
- Causal factors: {report['content']['causal_factors']['new_week']}
- Documents generated: {report['documents']['generated_week']}

Storage:
- Total files: {report['storage']['total_files']}
- Total size: {report['storage']['total_size_mb']} MB

Full report available at: {report_path}
                """
                
                send_email_notification_async.delay(admin.id, subject, body)
            
            return {
                'status': 'success',
                'report_path': str(report_path),
                'summary': {
                    'active_users': active_users_week,
                    'active_projects': active_projects_week,
                    'new_content': new_evidence_week + new_timeline_week + new_causal_week
                },
                'message': 'Usage report generated successfully'
            }
            
    except Exception as e:
        logger.error(f"Error generating usage report: {str(e)}")
        raise


@celery_app.task(bind=True)
def backup_database_async(self) -> Dict[str, Any]:
    """
    Create database backup.
    
    Returns:
        Dictionary with backup information
    """
    try:
        logger.info("Starting database backup")
        
        # Create backup directory
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        with celery_app.app.app_context():
            db_url = celery_app.app.config.get('SQLALCHEMY_DATABASE_URI')
            
            if 'sqlite' in db_url:
                # SQLite backup
                import sqlite3
                
                # Extract database path from URL
                db_path = db_url.replace('sqlite:///', '')
                backup_path = backup_dir / f"ioagent_backup_{timestamp}.db"
                
                # Create backup
                source = sqlite3.connect(db_path)
                dest = sqlite3.connect(str(backup_path))
                
                with dest:
                    source.backup(dest)
                
                source.close()
                dest.close()
                
                backup_size = backup_path.stat().st_size
                
            elif 'postgresql' in db_url:
                # PostgreSQL backup using pg_dump
                import subprocess
                from urllib.parse import urlparse
                
                parsed = urlparse(db_url)
                backup_path = backup_dir / f"ioagent_backup_{timestamp}.sql"
                
                # Build pg_dump command
                cmd = [
                    'pg_dump',
                    '-h', parsed.hostname or 'localhost',
                    '-p', str(parsed.port or 5432),
                    '-U', parsed.username,
                    '-d', parsed.path.lstrip('/'),
                    '-f', str(backup_path)
                ]
                
                # Set password through environment
                env = os.environ.copy()
                if parsed.password:
                    env['PGPASSWORD'] = parsed.password
                
                # Run backup
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr}")
                
                backup_size = backup_path.stat().st_size
                
            else:
                raise ValueError(f"Unsupported database type: {db_url}")
            
            # Compress backup
            compressed_path = backup_path.with_suffix('.gz')
            
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed backup
            backup_path.unlink()
            
            compressed_size = compressed_path.stat().st_size
            compression_ratio = (1 - compressed_size / backup_size) * 100
            
            # Clean old backups (keep last 7)
            backups = sorted(backup_dir.glob('ioagent_backup_*.gz'))
            if len(backups) > 7:
                for old_backup in backups[:-7]:
                    old_backup.unlink()
            
            logger.info(f"Database backup completed: {compressed_path}")
            
            return {
                'status': 'success',
                'backup_path': str(compressed_path),
                'original_size_mb': round(backup_size / 1024 / 1024, 2),
                'compressed_size_mb': round(compressed_size / 1024 / 1024, 2),
                'compression_ratio': round(compression_ratio, 1),
                'message': f'Database backed up successfully ({compressed_size / 1024 / 1024:.2f} MB)'
            }
            
    except Exception as e:
        logger.error(f"Error during database backup: {str(e)}")
        raise


@celery_app.task(bind=True)
def optimize_database_async(self) -> Dict[str, Any]:
    """
    Optimize database performance.
    
    Returns:
        Dictionary with optimization results
    """
    try:
        logger.info("Starting database optimization")
        
        with celery_app.app.app_context():
            db_url = celery_app.app.config.get('SQLALCHEMY_DATABASE_URI')
            
            if 'sqlite' in db_url:
                # SQLite optimization
                db.session.execute('VACUUM')
                db.session.execute('ANALYZE')
                db.session.commit()
                
                optimization_actions = ['VACUUM', 'ANALYZE']
                
            elif 'postgresql' in db_url:
                # PostgreSQL optimization
                # Note: VACUUM FULL requires exclusive lock
                db.session.execute('VACUUM ANALYZE')
                db.session.commit()
                
                # Update statistics
                tables = ['users', 'projects', 'evidence', 'timeline_entries', 'causal_factors']
                for table in tables:
                    try:
                        db.session.execute(f'ANALYZE {table}')
                    except Exception as e:
                        logger.warning(f"Could not analyze table {table}: {str(e)}")
                
                db.session.commit()
                optimization_actions = ['VACUUM ANALYZE', 'UPDATE STATISTICS']
                
            else:
                return {
                    'status': 'skipped',
                    'message': 'Database optimization not supported for this database type'
                }
            
            logger.info("Database optimization completed")
            
            return {
                'status': 'success',
                'actions': optimization_actions,
                'message': 'Database optimized successfully'
            }
            
    except Exception as e:
        logger.error(f"Error during database optimization: {str(e)}")
        raise


@celery_app.task(bind=True)
def check_system_health_async(self) -> Dict[str, Any]:
    """
    Check overall system health.
    
    Returns:
        Dictionary with health status
    """
    try:
        logger.info("Performing system health check")
        
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check database connectivity
        try:
            with celery_app.app.app_context():
                db.session.execute('SELECT 1')
                health_status['components']['database'] = {
                    'status': 'healthy',
                    'message': 'Database connection successful'
                }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check file storage
        try:
            upload_folder = Path(celery_app.app.config.get('UPLOAD_FOLDER', 'static/uploads'))
            if upload_folder.exists() and os.access(upload_folder, os.W_OK):
                health_status['components']['storage'] = {
                    'status': 'healthy',
                    'message': 'File storage accessible'
                }
            else:
                health_status['components']['storage'] = {
                    'status': 'unhealthy',
                    'message': 'File storage not accessible'
                }
                health_status['overall_status'] = 'degraded'
        except Exception as e:
            health_status['components']['storage'] = {
                'status': 'unhealthy',
                'message': f'Storage error: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check Redis connectivity (for Celery)
        try:
            from redis import Redis
            redis_url = celery_app.app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(redis_url)
            redis_client.ping()
            health_status['components']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            health_status['components']['redis'] = {
                'status': 'unhealthy',
                'message': f'Redis error: {str(e)}'
            }
            health_status['overall_status'] = 'degraded'
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_percentage = (free / total) * 100
            
            if free_percentage < 10:
                health_status['components']['disk_space'] = {
                    'status': 'unhealthy',
                    'message': f'Low disk space: {free_percentage:.1f}% free',
                    'free_gb': round(free / 1024 / 1024 / 1024, 2)
                }
                health_status['overall_status'] = 'degraded'
            else:
                health_status['components']['disk_space'] = {
                    'status': 'healthy',
                    'message': f'Disk space OK: {free_percentage:.1f}% free',
                    'free_gb': round(free / 1024 / 1024 / 1024, 2)
                }
        except Exception as e:
            health_status['components']['disk_space'] = {
                'status': 'unknown',
                'message': f'Could not check disk space: {str(e)}'
            }
        
        # Log health status
        if health_status['overall_status'] != 'healthy':
            logger.warning(f"System health check: {health_status['overall_status']}")
        else:
            logger.info("System health check: all components healthy")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'error',
            'message': f'Health check failed: {str(e)}'
        }
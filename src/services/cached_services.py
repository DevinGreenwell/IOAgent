"""Cached service layer for improved performance."""

import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta

from src.utils.cache import cached, invalidate_project_cache, cache_manager
from src.models.project import Project
from src.models.evidence import Evidence
from src.models.timeline_entry import TimelineEntry
from src.models.causal_factor import CausalFactor
from src.models.user import User
from src.services.anthropic_assistant import AnthropicAssistant

logger = logging.getLogger(__name__)


class CachedProjectService:
    """Service layer with caching for project operations."""
    
    @staticmethod
    @cached(expire=timedelta(minutes=15), prefix="project")
    def get_project_summary(project_id: int) -> Optional[Dict[str, Any]]:
        """Get cached project summary."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return None
            
            # Get counts
            evidence_count = Evidence.query.filter_by(project_id=project_id).count()
            timeline_count = TimelineEntry.query.filter_by(project_id=project_id).count()
            causal_count = CausalFactor.query.filter_by(project_id=project_id).count()
            
            # Get recent activity
            recent_evidence = Evidence.query.filter_by(project_id=project_id)\
                                          .order_by(Evidence.uploaded_at.desc())\
                                          .limit(5).all()
            
            recent_timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                                .order_by(TimelineEntry.created_at.desc())\
                                                .limit(5).all()
            
            return {
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                    'vessel_info': project.vessel_info,
                    'incident_info': project.incident_info
                },
                'statistics': {
                    'evidence_count': evidence_count,
                    'timeline_count': timeline_count,
                    'causal_count': causal_count
                },
                'recent_activity': {
                    'evidence': [
                        {
                            'id': e.id,
                            'title': e.title,
                            'uploaded_at': e.uploaded_at.isoformat()
                        } for e in recent_evidence
                    ],
                    'timeline': [
                        {
                            'id': t.id,
                            'description': t.description,
                            'timestamp': t.timestamp.isoformat()
                        } for t in recent_timeline
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error getting project summary: {str(e)}")
            return None
    
    @staticmethod
    @cached(expire=timedelta(minutes=30), prefix="timeline")
    def get_project_timeline(project_id: int) -> List[Dict[str, Any]]:
        """Get cached project timeline."""
        try:
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                        .order_by(TimelineEntry.timestamp).all()
            
            return [
                {
                    'id': entry.id,
                    'timestamp': entry.timestamp.isoformat(),
                    'description': entry.description,
                    'event_type': entry.event_type,
                    'location': entry.location,
                    'actors': entry.actors,
                    'significance': entry.significance,
                    'evidence_ids': entry.evidence_ids,
                    'created_at': entry.created_at.isoformat()
                } for entry in timeline
            ]
        except Exception as e:
            logger.error(f"Error getting project timeline: {str(e)}")
            return []
    
    @staticmethod
    @cached(expire=timedelta(minutes=30), prefix="causal")
    def get_causal_analysis(project_id: int) -> Dict[str, Any]:
        """Get cached causal analysis."""
        try:
            factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            # Group by category
            by_category = {}
            for factor in factors:
                category = factor.category or 'Uncategorized'
                if category not in by_category:
                    by_category[category] = []
                
                by_category[category].append({
                    'id': factor.id,
                    'description': factor.description,
                    'barrier_type': factor.barrier_type,
                    'remedial_action': factor.remedial_action,
                    'evidence_ids': factor.evidence_ids,
                    'contributing_factors': factor.contributing_factors
                })
            
            return {
                'total_factors': len(factors),
                'by_category': by_category,
                'categories': list(by_category.keys())
            }
        except Exception as e:
            logger.error(f"Error getting causal analysis: {str(e)}")
            return {
                'total_factors': 0,
                'by_category': {},
                'categories': []
            }
    
    @staticmethod
    def invalidate_project(project_id: int):
        """Invalidate all caches for a project."""
        invalidate_project_cache(project_id)
        
        # Clear specific service caches
        CachedProjectService.get_project_summary.clear_cache(project_id)
        CachedProjectService.get_project_timeline.clear_cache(project_id)
        CachedProjectService.get_causal_analysis.clear_cache(project_id)


class CachedUserService:
    """Service layer with caching for user operations."""
    
    @staticmethod
    @cached(expire=timedelta(hours=1), prefix="user")
    def get_user_projects(user_id: int) -> List[Dict[str, Any]]:
        """Get cached list of user's projects."""
        try:
            projects = Project.query.filter_by(owner_id=user_id)\
                                  .order_by(Project.updated_at.desc()).all()
            
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'created_at': p.created_at.isoformat(),
                    'updated_at': p.updated_at.isoformat() if p.updated_at else None,
                    'evidence_count': Evidence.query.filter_by(project_id=p.id).count(),
                    'timeline_count': TimelineEntry.query.filter_by(project_id=p.id).count()
                } for p in projects
            ]
        except Exception as e:
            logger.error(f"Error getting user projects: {str(e)}")
            return []
    
    @staticmethod
    @cached(expire=timedelta(hours=2), prefix="user")
    def get_user_statistics(user_id: int) -> Dict[str, Any]:
        """Get cached user statistics."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {}
            
            project_count = Project.query.filter_by(owner_id=user_id).count()
            
            # Get total evidence across all projects
            total_evidence = 0
            total_timeline = 0
            total_causal = 0
            
            projects = Project.query.filter_by(owner_id=user_id).all()
            for project in projects:
                total_evidence += Evidence.query.filter_by(project_id=project.id).count()
                total_timeline += TimelineEntry.query.filter_by(project_id=project.id).count()
                total_causal += CausalFactor.query.filter_by(project_id=project.id).count()
            
            return {
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'member_since': user.created_at.isoformat(),
                'statistics': {
                    'total_projects': project_count,
                    'total_evidence': total_evidence,
                    'total_timeline_entries': total_timeline,
                    'total_causal_factors': total_causal
                }
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {}


class CachedAIService:
    """Service layer with caching for AI operations."""
    
    def __init__(self):
        self.ai_assistant = AnthropicAssistant()
    
    @cached(expire=timedelta(hours=24), prefix="ai_suggestions")
    def get_timeline_suggestions(self, project_id: int, context: str) -> List[Dict[str, Any]]:
        """Get cached timeline suggestions."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return []
            
            # Get existing timeline for context
            existing_timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                                  .order_by(TimelineEntry.timestamp).all()
            
            # Get evidence for context
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            
            # Generate suggestions using AI
            suggestions = self.ai_assistant.suggest_timeline_events(
                project=project,
                existing_timeline=existing_timeline,
                evidence=evidence,
                focus_area=context
            )
            
            return suggestions
        except Exception as e:
            logger.error(f"Error getting timeline suggestions: {str(e)}")
            return []
    
    @cached(expire=timedelta(hours=24), prefix="ai_analysis")
    def get_causal_analysis_suggestions(self, project_id: int, 
                                      incident_type: Optional[str] = None) -> Dict[str, Any]:
        """Get cached causal analysis suggestions."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {}
            
            # Get all relevant data
            timeline = TimelineEntry.query.filter_by(project_id=project_id)\
                                        .order_by(TimelineEntry.timestamp).all()
            evidence = Evidence.query.filter_by(project_id=project_id).all()
            existing_factors = CausalFactor.query.filter_by(project_id=project_id).all()
            
            # Generate analysis using AI
            analysis = self.ai_assistant.analyze_causal_chain(
                project=project,
                timeline=timeline,
                evidence=evidence,
                existing_factors=existing_factors,
                incident_type=incident_type
            )
            
            return analysis
        except Exception as e:
            logger.error(f"Error getting causal analysis suggestions: {str(e)}")
            return {}


class CacheStatisticsService:
    """Service for cache statistics and monitoring."""
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get cache statistics and info."""
        try:
            if not cache_manager.is_available():
                return {
                    'status': 'unavailable',
                    'message': 'Cache service is not available'
                }
            
            # Get Redis info
            info = cache_manager.client.info()
            
            # Get memory stats
            memory_info = cache_manager.client.info('memory')
            
            # Count keys by pattern
            project_keys = len(cache_manager.client.keys('ioagent:project:*'))
            user_keys = len(cache_manager.client.keys('ioagent:user:*'))
            ai_keys = len(cache_manager.client.keys('ioagent:ai_*'))
            
            return {
                'status': 'healthy',
                'server': {
                    'version': info.get('redis_version'),
                    'uptime_seconds': info.get('uptime_in_seconds'),
                    'connected_clients': info.get('connected_clients')
                },
                'memory': {
                    'used_memory_human': memory_info.get('used_memory_human'),
                    'used_memory_peak_human': memory_info.get('used_memory_peak_human'),
                    'total_system_memory_human': memory_info.get('total_system_memory_human')
                },
                'keys': {
                    'total': cache_manager.client.dbsize(),
                    'project_keys': project_keys,
                    'user_keys': user_keys,
                    'ai_keys': ai_keys
                }
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def clear_all_cache() -> bool:
        """Clear all cache entries (use with caution)."""
        try:
            if cache_manager.is_available():
                cache_manager.client.flushdb()
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
"""Add performance indexes to database tables.

This migration adds indexes to foreign keys and frequently queried columns
to improve query performance.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add indexes for better performance."""
    
    # Projects table indexes
    op.create_index('idx_projects_user_id', 'projects', ['user_id'])
    op.create_index('idx_projects_status', 'projects', ['status'])
    op.create_index('idx_projects_created_at', 'projects', ['created_at'])
    
    # Timeline entries indexes
    op.create_index('idx_timeline_project_id', 'timeline_entries', ['project_id'])
    op.create_index('idx_timeline_timestamp', 'timeline_entries', ['timestamp'])
    op.create_index('idx_timeline_type', 'timeline_entries', ['entry_type'])
    op.create_index('idx_timeline_project_timestamp', 'timeline_entries', ['project_id', 'timestamp'])
    
    # Evidence table indexes
    op.create_index('idx_evidence_project_id', 'evidence', ['project_id'])
    op.create_index('idx_evidence_upload_date', 'evidence', ['upload_date'])
    
    # Causal factors indexes
    op.create_index('idx_causal_project_id', 'causal_factors', ['project_id'])
    op.create_index('idx_causal_category', 'causal_factors', ['category'])
    
    # Analysis sections indexes
    op.create_index('idx_analysis_project_id', 'analysis_sections', ['project_id'])
    op.create_index('idx_analysis_type', 'analysis_sections', ['section_type'])
    
    # Users table indexes
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

def downgrade():
    """Remove performance indexes."""
    
    # Remove users indexes
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_username', 'users')
    
    # Remove analysis sections indexes
    op.drop_index('idx_analysis_type', 'analysis_sections')
    op.drop_index('idx_analysis_project_id', 'analysis_sections')
    
    # Remove causal factors indexes
    op.drop_index('idx_causal_category', 'causal_factors')
    op.drop_index('idx_causal_project_id', 'causal_factors')
    
    # Remove evidence indexes
    op.drop_index('idx_evidence_upload_date', 'evidence')
    op.drop_index('idx_evidence_project_id', 'evidence')
    
    # Remove timeline indexes
    op.drop_index('idx_timeline_project_timestamp', 'timeline_entries')
    op.drop_index('idx_timeline_type', 'timeline_entries')
    op.drop_index('idx_timeline_timestamp', 'timeline_entries')
    op.drop_index('idx_timeline_project_id', 'timeline_entries')
    
    # Remove project indexes
    op.drop_index('idx_projects_created_at', 'projects')
    op.drop_index('idx_projects_status', 'projects')
    op.drop_index('idx_projects_user_id', 'projects')
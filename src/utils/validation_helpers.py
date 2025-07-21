"""Helper functions for validation."""

import re
from typing import Optional

def validate_project_id_format(project_id: str) -> bool:
    """Validate project ID format for string UUIDs."""
    if not project_id or not isinstance(project_id, str):
        return False
    if len(project_id) > 100:
        return False
    # Allow UUID format and alphanumeric with hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
        return False
    if '..' in project_id or '/' in project_id or '\\' in project_id:
        return False
    return True

def validate_timeline_entry_type(entry_type: str) -> bool:
    """Validate timeline entry type."""
    return entry_type in ['action', 'condition', 'event']

def validate_project_status(status: str) -> bool:
    """Validate project status."""
    return status in ['draft', 'in_progress', 'complete']

def validate_date_string(date_string: str) -> bool:
    """Validate ISO format date string."""
    try:
        from datetime import datetime
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False
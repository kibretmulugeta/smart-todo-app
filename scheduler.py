from datetime import datetime, timedelta
from typing import Dict, List, Optional

def calculate_next_due(time_config: Dict) -> str:
    """Calculate when this task is next due"""
    config_type = time_config.get('type')
    
    if config_type == 'once':
        return time_config.get('scheduled_datetime')
    
    elif config_type == 'duration':
        start = datetime.fromisoformat(time_config.get('start_datetime'))
        value = time_config.get('duration_value')
        unit = time_config.get('duration_unit')
        
        if unit == 'hours':
            due = start + timedelta(hours=value)
        elif unit == 'days':
            due = start + timedelta(days=value)
        elif unit == 'weeks':
            due = start + timedelta(weeks=value)
        else:
            due = start
        
        return due.isoformat()
    
    elif config_type == 'recurring':
        return time_config.get('start_datetime')
    
    return datetime.now().isoformat()

def generate_recurring_dates(time_config: Dict, limit: int = 10) -> List[str]:
    """Generate next N recurring dates based on pattern"""
    dates = []
    pattern = time_config.get('pattern')
    start = datetime.fromisoformat(time_config.get('start_datetime'))
    interval = time_config.get('interval', 1)
    unit = time_config.get('unit', 'days')
    end_date = time_config.get('end_datetime')
    max_occurrences = time_config.get('max_occurrences')
    bound = time_config.get('bound', {})
    
    current = start
    
    for _ in range(limit):
        # Check bounds if specified
        if bound:
            bound_start = bound.get('start')
            bound_end = bound.get('end')
            
            if bound_start and current < datetime.fromisoformat(bound_start):
                current = datetime.fromisoformat(bound_start)
            if bound_end and current > datetime.fromisoformat(bound_end):
                break
        
        # Check if we've hit the end date
        if end_date and current > datetime.fromisoformat(end_date):
            break
        
        # Check max occurrences
        if max_occurrences and len(dates) >= max_occurrences:
            break
        
        dates.append(current.isoformat())
        
        # Calculate next occurrence
        if pattern == 'daily':
            current += timedelta(days=interval)
        elif pattern == 'weekly':
            current += timedelta(weeks=interval)
        elif pattern == 'custom':
            if unit == 'hours':
                current += timedelta(hours=interval)
            elif unit == 'days':
                current += timedelta(days=interval)
            elif unit == 'weeks':
                current += timedelta(weeks=interval)
    
    return dates

def is_within_bound(check_date: datetime, bound: Dict) -> bool:
    """Check if a date falls within time bounds"""
    if not bound:
        return True
    
    bound_start = bound.get('start')
    bound_end = bound.get('end')
    
    if bound_start and check_date < datetime.fromisoformat(bound_start):
        return False
    if bound_end and check_date > datetime.fromisoformat(bound_end):
        return False
    
    return True
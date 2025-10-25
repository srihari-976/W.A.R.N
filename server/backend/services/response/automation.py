import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def create_automation_workflow(name: str, description: str, trigger_conditions: Dict[str, Any], 
                             actions: List[Dict[str, Any]], enabled: bool = True) -> Dict[str, Any]:
    """Create automation workflow for response actions"""
    try:
        workflow = {
            'id': f"workflow_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'name': name,
            'description': description,
            'trigger_conditions': trigger_conditions,
            'actions': actions,
            'enabled': enabled,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        logger.info(f"Created automation workflow: {name}")
        return workflow
        
    except Exception as e:
        logger.error(f"Error creating automation workflow: {e}")
        raise
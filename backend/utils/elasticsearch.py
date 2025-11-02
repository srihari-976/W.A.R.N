from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from backend.utils.logging import get_logger

logger = get_logger(__name__)

def get_elasticsearch_client():
    """Get Elasticsearch client with error handling"""
    try:
        es = Elasticsearch(
            hosts=['http://localhost:9200'],
            verify_certs=False,
            timeout=30
        )
        if es.ping():
            return es
        else:
            logger.warning("Elasticsearch is not responding")
            return None
    except ConnectionError as e:
        logger.warning(f"Could not connect to Elasticsearch: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Elasticsearch: {str(e)}")
        return None 